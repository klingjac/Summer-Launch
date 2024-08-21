import threading
import time
import logging
import os
# Imports for lora:
import busio
import board
import adafruit_rfm9x
import datetime
from digitalio import DigitalInOut, Direction, Pull
from lib.encode import encode_rap
from lib.RTC_Driver import RV_8803

from ads_main_pniwd import ADSSensorDataLogger
from opv_class import OPV
from QM_class import QuadMag_logger
from general_data import Status_Data

try:

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

except: 

    os.system("sudo reboot now")

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

def write_to_log_file(log_file, message):
    with open(log_file, 'a') as file:
        file.write(message + '\n')


class Beacon_Transmitter:
    def __init__(self, instances, logger, rtc):
        self.instances = instances
        self.logger = logger
        self.running = True
        self.last_telem = time.time()
        self.beacon = bytes(0)
        self.alive_flag = threading.Event()
        self.alive_flag.set()
        self.RTC = rtc

    def run(self):
        while self.running:
            try:
                start = time.time()
                self.alive_flag.set()
                try:
                    free_memory = self.instances["Status"].free_memory
                    free_storage = self.instances["Status"].free_disk_space
                except:
                    free_memory = 0
                    free_storage = 0
                try:
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
                except:
                    CPUtemp = 0
                    Vbattraw = 0
                    Ibattraw = 0
                    V3v3 = 0
                    I3v3 = 0
                    V5v = 0
                    I5v = 0
                    Vbatt = 0
                    Ibatt = 0
                    T3v3 = 0
                    T5v = 0
                try:
                    batt_temp = self.instances["Status"].tmp102_temp
                    bmetemp = self.instances["Status"].bme680_temp
                    bmepressure = self.instances["Status"].bme680_pressure
                except:
                    batt_temp = 0
                    bmetemp = 0
                    bmepressure = 0

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
                try:
                    recent_sweep_time = self.instances["OPV"].recent_sweep_time
                    #print(f"recent sweep time: {recent_sweep_time}")
                    ref_Voc = self.instances["OPV"].ref_Voc
                    #print(f"rev voc: {ref_Voc}")
                    opv_Voc = self.instances["OPV"].opv_Voc
                    #print(f"open voc: {opv_Voc}")
                    opv_Isc = self.instances["OPV"].opv_Isc
                    #print(f"open Isc: {opv_Isc}")
                except:
                    recent_sweep_time = 0
                    ref_Voc = 0
                    opv_Voc = 0
                    opv_Isc = 0
                try:
                    GPSfix = self.instances["ADS"].ads_sensors.GPS.gps_data['fix']
                    # % operations to assert datetime bounds
                    seconds = int(self.RTC.getSeconds())
                    seconds = seconds % 60
                    minutes = int(self.RTC.getMinutes())
                    minutes = minutes % 60
                    hours = int(self.RTC.getHours())
                    hours = hours % 24
                    #print(f"hours: {hours}")
                    day = int(self.RTC.getDate())
                    month = int(self.RTC.getMonth())
                    year = int(self.RTC.getYear()) + 2000  # Assuming the RTC returns year as two digits

                    # Create a datetime object from the RTC time
                    rtc_time = datetime.datetime(year, month, day, hours, minutes, seconds)

                    # Convert the datetime object to Unix time
                    UNIXtime = int(time.mktime(rtc_time.timetuple()))
                except:
                    UNIXtime = 1723563543
                try:
                    GPSnumSats = self.instances["ADS"].ads_sensors.GPS.gps_data['num_sv']
                    Alt = self.instances["ADS"].ads_sensors.GPS.gps_data['altitude']
                    Lat = self.instances["ADS"].ads_sensors.GPS.gps_data['latitude']
                    Long = self.instances["ADS"].ads_sensors.GPS.gps_data['longitude']
                    loggingCN0 = self.instances["ADS"].ads_sensors.GPS.gps_data['snr']
                except:
                    GPSnumSats = 0
                    Alt = 0
                    Lat = 0
                    Long = 0
                    loggingCN0 = 0
                try: 
                    magx = self.instances["ADS"].ads_sensors.magX
                    magy = self.instances["ADS"].ads_sensors.magY
                    magz = self.instances["ADS"].ads_sensors.magZ
                except: 
                    magx = 0
                    magy = 0
                    magz = 0
                try:
                    gyrox = self.instances["ADS"].ads_sensors.gyroX
                    gyroy = self.instances["ADS"].ads_sensors.gyroY
                    gyroz = self.instances["ADS"].ads_sensors.gyroZ
                except:
                    gyrox = 0
                    gyroy = 0
                    gyroz = 0
                try:
                    tridiode1 = self.instances["ADS"].ads_sensors.tri1b
                    tridiode2 = self.instances["ADS"].ads_sensors.tri2b
                    tridiode3 = self.instances["ADS"].ads_sensors.tri3b
                except:
                    tridiode1 = 0
                    tridiode2 = 0
                    tridiode3 = 0

                try:
                    telemetry_list_nums = [free_memory, free_storage, CPUtemp, Vbattraw, Ibattraw, V3v3, I3v3, V5v, I5v, Vbatt, Ibatt, T3v3, T5v, batt_temp, bmetemp, bmepressure, mag1x, mag1y, mag1z, mag2x, mag2y, mag2z, mag3x, mag3y, mag3z, mag4x, mag4y, mag4z, QMtemp, recent_sweep_time, ref_Voc, opv_Voc, opv_Isc, GPSfix, UNIXtime, GPSnumSats, Alt, Lat, Long, loggingCN0, magx, magy, magz, gyrox, gyroy, gyroz, tridiode1, tridiode2, tridiode3]
                except Exception as e:
                    telemetry_list_nums = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                    pass
                #print(f"Telem list: {telemetry_list_nums}")
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
                        #print(f"beacon length: {len(self.beacon)}")
                    except Exception as e:
                        self.beacon = bytes(0)
                        pass

                rap = encode_rap(BEACON_FLAG, self.beacon)  # add RAP packets
                #print(rap)
                if beacon_enabled:
                    downlink_telemetry_beacon(rap)
                    packet = None

                end = time.time()
                elapsed_time = end - start
                sleep_time = beacon_interval - elapsed_time
                if sleep_time > 0:
                    time.sleep(sleep_time)
            except Exception as e:
                write_to_log_file('/home/logger/flight_logging/Beacon_logs/Beacon_log.txt', str(e))
                return


class Watchdog:
    def __init__(self, logger):
        self.logger = logger
        self.instances = {}
        self.threads = {}
        self.beacon_transmitter = None
        self.RTC = RV_8803()

    def monitor(self):
        ADS = 0
        OPV = 0
        Beacon = 0
        General = 0


        while True:
            try:
                for name, instance in self.instances.items():
                    if instance == None:
                        print("Nonetype Instance")
                        continue
                    if not instance.alive_flag.is_set():
                        self.logger.info(f"{name} thread died. Restarting...")
                        time.sleep(2)
                        instance.stop()
                        self.threads[name].join()  # Ensure the thread has finished
                        self.instances[name] = self.spawn_instance(name)
                        if name == "ADS":
                            ADS += 1
                        elif name == "OPV":
                            OPV += 1
                        elif name == "Status":
                            General += 1
                    instance.alive_flag.clear()

                if not self.beacon_transmitter.alive_flag.is_set():
                    self.logger.info("Beacon_Transmitter thread died. Restarting...")
                    self.beacon_transmitter.stop()
                    self.threads["Beacon_Transmitter"].join()
                    self.start_beacon_transmitter()
                    Beacon += 1

                time.sleep(60)  # Adjust the sleep duration as needed

                if ADS == 5 or OPV == 5 or Beacon == 5 or General == 5:
                    print(f"Watchdog reboot 1: ADS: {ADS}, OPV: {OPV}, Beacon: {Beacon}, General: {General}")
                    os.system("sudo reboot now")
                    
            except Exception as e:
                print(f"Watchdog reboot 2 -- Error: {e}")
                os.system("sudo reboot now")

    def spawn_instance(self, name):
        try:
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
        except Exception as e:
            print(f"Error Starting instance: {e}")
            return None

    def start_beacon_transmitter(self):
        self.beacon_transmitter = Beacon_Transmitter(self.instances, self.logger, rtc = self.RTC)
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
    try: 
        main()
    except Exception as e:
        print(f"Big Fatal Error: {e}")
        os.system("sudo reboot now")
        
