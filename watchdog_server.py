import threading
import time
import logging
#Imports for lora:
import busio
import board
import adafruit_rfm9x
from datetime import datetime
from digitalio import DigitalInOut, Direction, Pull

from ads_main_pniwd import ADSSensorDataLogger
from opv_class import OPV
from QM_class import QuadMag_logger
from general_data import Status_Data

#LoRa Tunable Parameters
beacon_interval = 5 # in seconds (beacon telemetry every X seconds)
uplink_wait_time = 6.0 # in seconds (wait for uplink for X seconds after downlinking a beacon)

#LoRa device set up
#CS = DigitalInOut(board.CE1) # init CS pin for SPI
#RESET = DigitalInOut(board.D25) # init RESET pin for the RFM9x module
#spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO) # init SPI
#rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, 437.0) # init object for the radio

# LoRa PHY settings
#rfm9x.tx_power = 23                 # TX power in dBm (23 dBm = 0.2 W) (TODO, default 13)
# rfm9x.signal_bandwidth = 62500    # High bandwidth => high data rate and low range (TODO, default 12500)
# rfm9x.coding_rate = 5               # Coding rate (TODO, default 5)
# rfm9x.spreading_factor = 12         # Spreading factor (TODO, default 7)
# rfm9x.enable_crc = True           # crc (TODO, default True)

# Variables to control beacon state and interval
beacon_enabled = True
#last_beacon_time = time.monotonic()

class Beacon_Transmitter:
    def __init__(self, instances, logger):
        self.instances = instances
        self.logger = logger
        self.running = True

    def run(self):
        while self.running:
            # for name, instance in self.instances.items():
            #     if instance:
            #         try:
            #             self.logger.info(f"Beacon from {name}: Alive")
            #             # Access and log specific details from the instance if needed
            #         except Exception as e:
            #             self.logger.error(f"Error accessing {name} instance: {e}")
            free_memory = self.instances["Status"].free_memory
            free_storage = self.instances["Status"].free_disk_space
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
            # Where am I pulling QM data from?
            mag1x
            mag1y
            mag1z
            mag2x
            mag2y
            mag2z
            mag3x
            mag3y
            mag3z
            mag4x
            mag4y
            mag4z
            QMtemp
            # Where am I pulling OPV data from?
            recent_sweep_time = OPV.recent_sweep_time
            ref_Voc = OPV.ref_Voc
            opv_Voc = OPV.opv_Voc
            opv_Isc = OPV.opv_Isc
            UNIXtime
            # Where am I pulling GPS data from?
            GPSnumSats
            Alt = 
            Lat
            loggingCN0
            magx
            magy
            magz
            gyrox
            gyroy
            gyroz
            tridiode1
            tridiode2
            tridiode3
            time.sleep(15)  # Adjust the beacon interval as needed

class Watchdog:
    def __init__(self, logger):
        self.logger = logger
        self.instances = {}
        self.threads = {}
        self.beacon_transmitter = None

    def monitor(self):
        while True:
            for name, instance in self.instances.items():
                if not instance.alive_flag.is_set():
                    self.logger.info(f"{name} thread died. Restarting...")
                    instance.stop()
                    self.threads[name].join()  # Ensure the thread has finished
                    self.instances[name] = self.spawn_instance(name)
                instance.alive_flag.clear()
                    
            time.sleep(15)  # Adjust the sleep duration as needed

    def spawn_instance(self, name):
        instance = None
        if name == "ADS":
            instance = ADSSensorDataLogger()
        elif name == "OPV":
            instance = OPV()
        elif name == "QuadMag":
            instance = QuadMag_logger()
        elif name == "Status":
            eps = Status_Data()  # Replace with your actual EPS object initialization
            instance = Status_Data(eps)
        
        thread = threading.Thread(target=instance.run)
        thread.start()
        self.threads[name] = thread

        self.logger.info(f"Started {name} thread with ID {thread.ident}")
        return instance

    def start_monitoring(self):
        for name in ["ADS", "OPV", "QuadMag", "Status"]:
            self.instances[name] = self.spawn_instance(name)
        
        # Start the Beacon_Transmitter
        self.beacon_transmitter = Beacon_Transmitter(self.instances, self.logger)
        beacon_thread = threading.Thread(target=self.beacon_transmitter.run)
        beacon_thread.start()
        self.threads["Beacon_Transmitter"] = beacon_thread

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
