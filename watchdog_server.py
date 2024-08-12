import threading
import time
import logging
# Imports for lora:
import busio
import board
import adafruit_rfm9x
from datetime import datetime
from digitalio import DigitalInOut, Direction, Pull
from lib.encode import encode_rap
from lib.RTC_Driver import RV_8803

from ads_main_pniwd import ADSSensorDataLogger
from opv_class import OPV
from QM_class import QuadMag_logger
from general_data import Status_Data

BEACON_FLAG = 0x03

# LoRa Tunable Parameters
beacon_interval = 10  # in seconds (beacon telemetry every X seconds)
uplink_wait_time = 2.0  # in seconds (wait for uplink for X seconds after downlinking a beacon)

# LoRa device set up
CS = DigitalInOut(board.CE1)  # init CS pin for SPI
RESET = DigitalInOut(board.D25)  # init RESET pin for the RFM9x module
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)  # init SPI
rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, 437.0)  # init object for the radio

# LoRa PHY settings
rfm9x.tx_power = 23  # TX power in dBm (23 dBm = 0.2 W) (TODO, default 13)
# rfm9x.signal_bandwidth = 62500  # High bandwidth => high data rate and low range (TODO, default 12500)
# rfm9x.coding_rate = 5  # Coding rate (TODO, default 5)
# rfm9x.spreading_factor = 12  # Spreading factor (TODO, default 7)
# rfm9x.enable_crc = True  # crc (TODO, default True)

# Variables to control beacon state and interval
beacon_enabled = True


def parse_magnetometer_data(data):
    # Define the keys for the dictionary
    keys = [
        'mag1x', 'mag1y', 'mag1z',
        'mag2x', 'mag2y', 'mag2z',
        'mag3x', 'mag3y', 'mag3z',
        'mag4x', 'mag4y', 'mag4z',
        'QMtemp'
    ]

    # If data is None, set all values to 0
    if data is None:
        mag_values = {key: 0.0 for key in keys}
    else:
        # Create a dictionary mapping the keys to the corresponding values starting from index 2
        mag_values = {keys[i]: float(data[i + 2]) for i in range(len(keys))}

    return mag_values


def downlink_telemetry_beacon(telemetry_data):
    if telemetry_data:
        print(f"this is telem data: {telemetry_data}")
        rfm9x.send(telemetry_data)
        print("Beacon sent.")
    else:
        print("Telemetry data is none")


def listen_for_commands(timeout=uplink_wait_time):
    # Listen for a specific amount of time (timeout) for incoming packets
    rfm9x.receive(timeout=timeout)


def handle_incoming_packet(packet):
    global beacon_enabled  # Needed to modify the global variable

    # Send ACK
    packet_decoded = str(packet, "utf-8")
    ack_msg = f'ACK_{packet_decoded}'
    rfm9x.send(bytes(ack_msg, 'utf-8'))

    # The commands we expect: Disable/Enable beaconing, request a big file downlink, or ping
    if packet == b'CMD_DISABLE_BEACON':
        beacon_enabled = False
        print("Beacon disabled")
    elif packet == b'CMD_ENABLE_BEACON':
        beacon_enabled = True
        print("Beacon enabled")
    elif packet == b'CMD_DOWNLINK_BIG_FILE':
        send_big_file()  # Implement this function with the actual logic to downlink a big file
        print("Big file requested for downlink")
    elif packet == b'CMD_PING':
        send_ping_response()
        print("Ping received and acknowledged")
        print()


def send_big_file():
    # Replace this with the logic to send a big file downlink
    print("Sending big file...")


def send_ping_response():
    # Send an acknowledgment back as a response to the ping
    ping_response_data = "PONG"
    rfm9x.send(bytes(ping_response_data, 'utf-8'))
    print("Ping response sent.")


prev_packet = None


class Beacon_Transmitter:
    def __init__(self, instances, logger):
        self.instances = instances
        self.logger = logger
        self.running = True
        self.last_telem = time.time()
        self.beacon = bytes(0)
        self.alive_flag = threading.Event()
        self.alive_flag.set()

    def run(self):
        while self.running:
            try:
                start = time.time()
                self.alive_flag.set()
                
                free_memory = self.instances["Status"].free_memory
                free_storage = self.instances["Status"].free_disk_space
                print(f"free storage: {free_storage}")
                CPUtemp = self.instances["Status"].cpu_temp
                Vbattraw = self.instances["Status"].VbattRaw
                Ibattraw = self.instances["Status"].IbattRaw
                V3v3 = self.instances["Status"].V3v3
                I3v3 = self.instances["Status"].I3v3
                V5v = self.instances["Status"].V5v0
                I5v = self.instances["Status"].I5v0
                Vbatt = self.instances["Status"].Vbatt
                Ibatt = self.instances["Status"].Ibatt
                T3v3 = self.instances["Status"].T3v3
                T5v = self.instances["Status"].T5v0
                batt_temp = self.instances["Status"].tmp102_temp
                bmetemp = self.instances["Status"].bme680_temp
                bmepressure = self.instances["Status"].bme680_pressure

                #dict = parse_magnetometer_data(self.instances["QuadMag"].QuadMag.current_reading)
                mag1x = 0 #dict["mag1x"]
                mag1y = 0 #dict["mag1y"]
                mag1z = 0 #dict["mag1z"]
                mag2x = 0 #dict["mag2x"]
                mag2y = 0 #dict["mag2y"]
                mag2z = 0 #dict["mag2z"]
                mag3x = 0 #dict["mag3x"]
                mag3y = 0 #dict["mag3y"]
                mag3z = 0 #dict["mag3z"]
                mag4x = 0 #dict["mag4x"]
                mag4y = 0 #dict["mag4y"]
                mag4z = 0 #dict["mag4z"]
                QMtemp = 0 #dict["QMtemp"]

                recent_sweep_time = self.instances["OPV"].recent_sweep_time
                print(f"recent sweep time: {recent_sweep_time}")
                ref_Voc = self.instances["OPV"].ref_Voc
                print(f"rev voc: {ref_Voc}")
                opv_Voc = self.instances["OPV"].opv_Voc
                print(f"open voc: {opv_Voc}")
                opv_Isc = self.instances["OPV"].opv_Isc
                print(f"open Isc: {opv_Isc}")

                GPSfix = self.instances["ADS"].ads_sensors.GPS.gps_data['fix']
                UNIXtime = 1722546568
                GPSnumSats = self.instances["ADS"].ads_sensors.GPS.gps_data['num_sv']
                Alt = self.instances["ADS"].ads_sensors.GPS.gps_data['altitude']
                Lat = self.instances["ADS"].ads_sensors.GPS.gps_data['latitude']
                Long = self.instances["ADS"].ads_sensors.GPS.gps_data['longitude']
                loggingCN0 = self.instances["ADS"].ads_sensors.GPS.gps_data['snr']
                magx = self.instances["ADS"].ads_sensors.magX
                magy = self.instances["ADS"].ads_sensors.magY
                magz = self.instances["ADS"].ads_sensors.magZ
                gyrox = self.instances["ADS"].ads_sensors.gyroX
                gyroy = self.instances["ADS"].ads_sensors.gyroY
                gyroz = self.instances["ADS"].ads_sensors.gyroZ
                tridiode1 = self.instances["ADS"].ads_sensors.tri1b
                tridiode2 = self.instances["ADS"].ads_sensors.tri2b
                tridiode3 = self.instances["ADS"].ads_sensors.tri3b

                try:
                    telemetry_list_nums = [free_memory, free_storage, CPUtemp, Vbattraw, Ibattraw, V3v3, I3v3, V5v, I5v, Vbatt, Ibatt, T3v3, T5v, batt_temp, bmetemp, bmepressure, mag1x, mag1y, mag1z, mag2x, mag2y, mag2z, mag3x, mag3y, mag3z, mag4x, mag4y, mag4z, QMtemp, recent_sweep_time, ref_Voc, opv_Voc, opv_Isc, GPSfix, UNIXtime, GPSnumSats, Alt, Lat, Long, loggingCN0, magx, magy, magz, gyrox, gyroy, gyroz, tridiode1, tridiode2, tridiode3]
                except Exception as e:
                    telemetry_list_nums = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                    pass
                print(f"Telem list: {telemetry_list_nums}")
                telem_time_elapsed = time.time() - self.last_telem
                if telem_time_elapsed > beacon_interval:
                    self.last_telem = time.time()

                    try:
                        
                        signed_unsigned = [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0]

                        #byte_lengths = [2, 2, 4, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 2, 2, 2, 2, 1, 4, 2, 2, 2, 2, 2, 1, 4, 2, 2, 2, 2, 2, 4, 4, 4, 4, 4, 4, 2, 2, 2]

                        byte_lengths = [2,2,4,2,2,2,2,2,2,2,2,2,2,2,2,2,4,4,4,4,4,4,4,4,4,4,4,4,4,2,2,2,2,1,4,2,2,2,2,2,4,4,4,4,4,4,2,2,2]
                        

                        conversion_funcs = [1*100, 1*100/1000, 1*100, 1*100, 1*100, 1*100, 1*100, 1*100, 1*100, 1*100, 1*100, 1*100, 1*100, 1*100, 1*100, 1*10, 1*1000, 1*1000, 1*1000, 1*1000, 1*1000, 1*1000, 1*1000, 1*1000, 1*1000, 1*1000, 1*1000, 1*1000, 1*10, 1*1000, (1*1000), (1*1000), 1*1000, 1, 1, 1, 1*100, 1*100, 1*100, 1, 1*100, 1*100, 1*100, 1*100, 1*100, 1*100, 1, 1, 1]

                        telemetry_list_bytes = []
                        for i, value in enumerate(telemetry_list_nums):
                            try:
                                byte_value = int(value * conversion_funcs[i]).to_bytes(byte_lengths[i], 'little', signed=signed_unsigned[i])
                            except:
                                byte_value = bytearray(byte_lengths[i])  # if cannot convert to bytes, create bytearray filled with 0s
                            telemetry_list_bytes.append(byte_value)

                        self.beacon = bytes().join(telemetry_list_bytes)
                        print(f"beacon length: {len(self.beacon)}")
                    except Exception as e:
                        self.beacon = bytes(0)
                        pass

                rap = encode_rap(BEACON_FLAG, self.beacon)  # add RAP packets
                print(rap)
                if beacon_enabled:
                    downlink_telemetry_beacon(rap)
                    packet = None

                end = time.time()
                elapsed_time = end - start
                sleep_time = beacon_interval - elapsed_time
                if sleep_time > 0:
                    time.sleep(sleep_time)
            except:
                print("Issue with beaconing")


class Watchdog:
    def __init__(self, logger):
        self.logger = logger
        self.instances = {}
        self.threads = {}
        self.beacon_transmitter = None
        self.RTC = RV_8803()

    def monitor(self):
        while True:
            try:
                for name, instance in self.instances.items():
                    if not instance.alive_flag.is_set():
                        self.logger.info(f"{name} thread died. Restarting...")
                        instance.stop()
                        self.threads[name].join()  # Ensure the thread has finished
                        self.instances[name] = self.spawn_instance(name)
                    instance.alive_flag.clear()

                if not self.beacon_transmitter.alive_flag.is_set():
                    self.logger.info("Beacon_Transmitter thread died. Restarting...")
                    self.beacon_transmitter.stop()
                    self.threads["Beacon_Transmitter"].join()
                    self.start_beacon_transmitter()

                time.sleep(60)  # Adjust the sleep duration as needed
            except:
                continue

    def spawn_instance(self, name):
        instance = None
        if name == "ADS":
            instance = ADSSensorDataLogger(rtc = self.RTC)
        elif name == "OPV":
            instance = OPV(rtc = self.RTC)
        #elif name == "QuadMag":
        #    instance = QuadMag_logger(self.RTC)
        elif name == "Status":
            #eps = Status_Data(self.RTC)  # Replace with your actual EPS object initialization
            instance = Status_Data(rtc = self.RTC)

        thread = threading.Thread(target=instance.run)
        thread.start()
        self.threads[name] = thread

        self.logger.info(f"Started {name} thread with ID {thread.ident}")
        return instance

    def start_beacon_transmitter(self):
        self.beacon_transmitter = Beacon_Transmitter(self.instances, self.logger)
        beacon_thread = threading.Thread(target=self.beacon_transmitter.run)
        beacon_thread.start()
        self.threads["Beacon_Transmitter"] = beacon_thread
        self.logger.info(f"Started Beacon_Transmitter thread with ID {beacon_thread.ident}")

    def start_monitoring(self):
        for name in ["ADS", "OPV", "Status"]:
            self.instances[name] = self.spawn_instance(name)

        self.start_beacon_transmitter()
        self.monitor()


def initialize_logger():
    logger = logging.getLogger('WatchdogLogger')
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler('watchdog_restarts.log')
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger


def main():
    logger = initialize_logger()
    watchdog = Watchdog(logger)
    watchdog.start_monitoring()


if __name__ == "__main__":
    main()
