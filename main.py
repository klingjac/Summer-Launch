from ads_main_pniwd import ADSSensorDataLogger
from opv_class import OPV
import time

def main():
    #Start all subsystem functions/loggers

    ADS_logger = ADSSensorDataLogger()

    OPV_logger = OPV() #Autostarts once the class is evoked

    while True:
        time.sleep(1)



    

if __name__ == "__main__":
    main()
