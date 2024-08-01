import threading
import time
import logging

class Watchdog:
    def __init__(self, logger):
        self.logger = logger
        self.instances = {}
        self.threads = {}

    def monitor(self):
        while True:
            for name, instance in self.instances.items():
                if not instance.alive_flag.is_set():
                    self.logger.info(f"{name} thread died. Restarting...")
                    self.instances[name].running = False
                    time.sleep(10)
                    self.instances[name] = self.spawn_instance(name)
                    
            time.sleep(15)  # Adjust the sleep duration as needed

    def spawn_instance(self, name):
        instance = None
        if name == "ADS":
            from ads_main_pniwd import ADSSensorDataLogger
            instance = ADSSensorDataLogger()
        elif name == "OPV":
            from opv_class import OPV
            instance = OPV()
        elif name == "QuadMag":
            from QM_class import QuadMag_logger
            instance = QuadMag_logger()

        thread = threading.Thread(target=instance.run)
        thread.start()
        self.threads[name] = thread

        self.logger.info(f"Started {name} thread with ID {thread.ident}")
        return instance

    def start_monitoring(self):
        for name in ["ADS", "OPV", "QuadMag"]:
            self.instances[name] = self.spawn_instance(name)
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
