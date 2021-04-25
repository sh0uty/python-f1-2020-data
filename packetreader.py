import socket
import sys
import keyboard
import logging
import selectors
from f1_2020_telemetry.packets import unpack_udp_packet, PacketID

"""
Packetreader Class

This class receives the data from F1 2020 UDP server with the help of f1-2020-telemetry package
"""

class PacketReader():
    def __init__(self, ip : str, port : int):
        self.ip = ip
        self.port = port
        self.frame = None
        self.frame_data = {}
        self.socketpair = socket.socketpair()

    # Quellen für Methode run:
        # Multiplexende Server https://openbook.rheinwerk-verlag.de/python/34_001.html#u34.1.8
    def run(self):

        # Initializing UDP socket
        sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        sock.bind((self.ip, self.port))

        logging.info(f"Packetreader started on port {self.port}")

        # Initializing selectors and registering UDP socket and one socket of the socketpair for exit signal
        selector = selectors.DefaultSelector()
        key_sock = selector.register(sock, selectors.EVENT_READ)
        key_socketpair = selector.register(self.socketpair[0], selectors.EVENT_READ)

        logging.info(f"Initialized selectors and keys. Going into main loop now")

        # Main Loop for receiving from UDP socket and checking if exit signal is send
        end = False
        while not end:
            for (key, mask) in selector.select():
                # Checking if UDP socket receives data
                if key == key_sock:
                    packed_packet = sock.recv(2048)
                    packet = unpack_udp_packet(packed_packet)
                    self.GetDataFromPacket(packet)
                # Checking if socket of socketpair receives data in order to exit main loop
                elif key == key_socketpair:
                    end = True

        logging.info("Packetreader main loop exit")

        # Close all sockets and selctors
        selector.close()
        sock.close()
        for s in self.socketpair:
            s.close()

        logging.info("Closed every connction")

    def GetDataFromPacket(self, packet):
        # Checking if the frame from the packet that is send is the same as the current packages frame
        # If not clear data
        if packet.header.frameIdentifier != self.frame:
            self.CreateDataForDisplay()
            self.frame = packet.header.frameIdentifier
            self.frame_data = {}
        
        # Store the new received package
        self.frame_data[PacketID(packet.header.packetId)] = packet

    def CreateDataForDisplay(self):
        # Checking if stored package is empty
        if not bool(self.frame_data):
            return

        # Combine all packages
        all_packets = next(iter(self.frame_data.values()))

        # TESTDATA

        player_car = all_packets.header.playerCarIndex

        try:
            if PacketID.CAR_TELEMETRY in self.frame_data:
                self.speed = \
                    ( self.frame_data[PacketID.CAR_TELEMETRY].carTelemetryData[player_car].speed )
                self.gear = \
                    ( self.frame_data[PacketID.CAR_TELEMETRY].carTelemetryData[player_car].gear )
                self.engineRPM = \
                    ( self.frame_data[PacketID.CAR_TELEMETRY].carTelemetryData[player_car].engineRPM )
                self.throttle = \
                    ( self.frame_data[PacketID.CAR_TELEMETRY].carTelemetryData[player_car].throttle )
                self.brake = \
                    ( self.frame_data[PacketID.CAR_TELEMETRY].carTelemetryData[player_car].brake )
                self.drs = \
                    ( self.frame_data[PacketID.CAR_TELEMETRY].carTelemetryData[player_car].drs )
                self.tyresInnerTemperature = \
                    ( self.frame_data[PacketID.CAR_TELEMETRY].carTelemetryData[player_car].tyresInnerTemperature )

            if PacketID.CAR_STATUS in self.frame_data:
                self.fuelRemainingLaps = \
                    ( self.frame_data[PacketID.CAR_STATUS].carStatusData[player_car].fuelRemainingLaps )
                self.ersStoreEnergy = \
                    ( self.frame_data[PacketID.CAR_STATUS].carStatusData[player_car].ersStoreEnergy )
                self.ersDeployMode = \
                    ( self.frame_data[PacketID.CAR_STATUS].carStatusData[player_car].ersDeployMode )
                self.ersDeployedThisLap = \
                    ( self.frame_data[PacketID.CAR_STATUS].carStatusData[player_car].ersDeployedThisLap )
                self.ersHarvestedThisLapMGUK = \
                    ( self.frame_data[PacketID.CAR_STATUS].carStatusData[player_car].ersHarvestedThisLapMGUK )
                self.ersHarvestedThisLapMGUH = \
                    ( self.frame_data[PacketID.CAR_STATUS].carStatusData[player_car].ersHarvestedThisLapMGUH )

            if PacketID.LAP_DATA in self.frame_data:
                self.lastLapTime = \
                    ( self.frame_data[PacketID.LAP_DATA].lapData[player_car].lastLapTime )
                self.currentLapTime = \
                    ( self.frame_data[PacketID.LAP_DATA].lapData[player_car].currentLapTime )
                self.bestLapTime = \
                    ( self.frame_data[PacketID.LAP_DATA].lapData[player_car].bestLapTime )
                self.carPosition = \
                    ( self.frame_data[PacketID.LAP_DATA].lapData[player_car].carPosition )
                self.currentLapNum = \
                    ( self.frame_data[PacketID.LAP_DATA].lapData[player_car].currentLapNum )

        except KeyError:
            logging.warning("Package could not be read correctly. Skipping!")

        

        print(f"Speed: {self.speed}, Gear: {self.gear}, RPM: {self.engineRPM}, Throttle: {self.throttle}, Brake: {self.brake}, DRS: {self.drs}, TyresInnterTemperature: {list(self.tyresInnerTemperature)}")
        #print(f"FuelRemainingLaps: {self.fuelRemainingLaps}, ErsStoreEnergy {self.ersStoreEnergy}, ErsDeployMode {self.ersDeployMode}, ErsDeployedThisLap {self.ersDeployedThisLap}. ErsHarvestedThisLapMGUK {self.ersHarvestedThisLapMGUK}, ErsHarvestedThisLapMGUH {self.ersHarvestedThisLapMGUH}")

        # END TESTDATA

    # Send end signal if q-key is pressed
    def endSignal(self):
        while True:
            if (keyboard.is_pressed('q')):
                logging.info("Q-key pressed. Attempting to quit now")
                self.socketpair[1].send(b'\x00')
                break;