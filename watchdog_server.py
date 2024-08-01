import threading
import time
import logging
from ads_main_pniwd import ADSSensorDataLogger
from opv_class import OPV
from QM_class import QuadMag_logger
from general_data import Status_Data

class Beacon_Transmitter:
    def __init__(self, instances, logger):
        self.instances = instances
        self.logger = logger
        self.running = True

    def run(self):
        while self.running:
            for name, instance in self.instances.items():
                if instance:
                    try:
                        self.logger.info(f"Beacon from {name}: Alive")
                        # Access and log specific details from the instance if needed
                    except Exception as e:
                        self.logger.error(f"Error accessing {name} instance: {e}")
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
