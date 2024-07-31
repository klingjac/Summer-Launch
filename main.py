from ads_main_pniwd import ADSSensorDataLogger
from opv_class import OPV
from watchdog_server import Watchdog
from QM_class import QuadMag_logger
import time

def main():
    #Start all subsystem functions/loggers

    ADS_logger = ADSSensorDataLogger()

    OPV_logger = OPV() #Autostarts once the class is evoked

    QM_logger = QuadMag_logger()

    watchdog = Watchdog()

    while True:
        time.sleep(1)



    

if __name__ == "__main__":
    main()
