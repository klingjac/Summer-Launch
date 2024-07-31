import multiprocessing
import time
import logging

def create_shared_heartbeat():
    return multiprocessing.Value('b', False)

def initialize_logger():
    logger = logging.getLogger('WatchdogLogger')
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler('watchdog_restarts.log')
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger

def watchdog_process(heartbeats, processes, logger):
    while True:
        for name, heartbeat in heartbeats.items():
            if not heartbeat.value:
                logger.info(f"{name} failed to send heartbeat. Restarting...")
                processes[name].terminate()
                processes[name].join()  # Ensure the process has terminated
                heartbeat.value = True  # Reset heartbeat before restarting
                process = spawn_process(name, heartbeats, logger)
                processes[name] = process
            else:
                heartbeat.value = False  # Reset heartbeat for the next check
        time.sleep(60)

def spawn_process(name, heartbeats, logger):
    if name == "ADS":
        from ads_main_pniwd import run_ads_logger
        process = multiprocessing.Process(target=run_ads_logger, args=(heartbeats[name],))
    elif name == "OPV":
        from opv_class import run_opv
        process = multiprocessing.Process(target=run_opv, args=(heartbeats[name],))
    elif name == "QuadMag":
        from QM_class import run_quadmag
        process = multiprocessing.Process(target=run_quadmag, args=(heartbeats[name],))
    process.start()
    logger.info(f"Started {name} process with PID {process.pid}")
    return process

def main():
    logger = initialize_logger()
    heartbeats = {
        "ADS": create_shared_heartbeat(),
        "OPV": create_shared_heartbeat(),
        "QuadMag": create_shared_heartbeat()
    }

    processes = {}
    for name in heartbeats.keys():
        processes[name] = spawn_process(name, heartbeats, logger)

    watchdog_process(heartbeats, processes, logger)

if __name__ == "__main__":
    main()
