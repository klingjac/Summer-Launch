import threading
import os
import time
import smbus2
from lib.MCP4725 import MCP4725
from busio import I2C
from lib.ADS1x15 import ADS1015
import csv
from datetime import datetime
import logging

def write_to_log_file(log_file, message):
    with open(log_file, 'a') as file:
        file.write(message + '\n')

def init_log_file(log_file, message):
    with open(log_file, 'w') as file:
        file.write(message + '\n')

class OPV:
    def __init__(self, rtc):
        # Initialize Sensor Members
        self.dac = MCP4725(address=0x60)
        self.nons = ADS1015(address=0x4a)
        self.shunted = ADS1015(address=0x48)
        self.refer = ADS1015(address=0x49)
        self.running = True
        self.alive_flag = threading.Event()
        self.alive_flag.set()
        self.ref_Voc = 0
        self.opv_Voc = 0
        self.opv_Isc = 0
        self.recent_sweep_time = 0
        # Directory Setup
        self.directory = "./OPV"
        os.makedirs(self.directory, exist_ok=True)
        self.RTC = rtc
        #init_log_file('/home/logger/flight_logging/OPV_logs/OPV_log.txt', "OPV Log")

    def generate_opv_file_name(self, directory):
        num_files = len([f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))])
        timestamp = self.RTC.getTime()
        file_name = f"{num_files}_{timestamp}.csv"
        return os.path.join(directory, file_name)

    def tocsv(self, filename, data):
        with open(filename, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(['step', 'A0read', 'A1read', 'A2read'])
            csvwriter.writerows(data)

    def start_stop_weened(self, filename=None):
        # Initialize logging
        logging.basicConfig(level=logging.INFO)

        # Start continuous conversion on channel 0 for all ADCs
        data = []
        self.nons.start_adc(channel=1, gain=1, data_rate=3300)
        self.shunted.start_adc(channel=0, gain=1, data_rate=3300)
        self.refer.start_adc(channel=2, gain=1, data_rate=3300)

        try:
            # Read conversion results for 5 seconds
            start = time.time()
            value = 0
            while value < 4096:
                self.dac.set_voltage(value)
                result1 = self.nons.get_last_result()
                result2 = self.shunted.get_last_result()
                result3 = self.refer.get_last_result()
                data.append([value, result1, result2, result3])

                if value < 1000:
                    value += 50
                elif value > 2700:
                    value += 50
                else:
                    value += 1

        finally:
            # Save output variables for beaconing
            #ref_Voc calc
            fourth_col = [row[3] for row in data]
            subset = fourth_col[1:10]
            self.ref_Voc = (sum(subset)/9)/250
            #opv_Voc calc
            second_col = [row[1] for row in data]
            subset = second_col[1:10]
            self.opv_Voc = (sum(subset)/9)/250
            #opv_Isc components calc
            third_col = [row[2] for row in data]
            subset = second_col[-9:]
            subset2 = third_col[-9:]
            # I_sc = (nonsh - shunted)/6.8
            opv_Vsc_ns = ((sum(subset)/9))/250
            opv_Vsc_s = ((sum(subset2)/9))/250
            self.opv_Isc = (((opv_Vsc_ns - opv_Vsc_s)/6.8))
            # Time output
            finished = time.time()
            self.recent_sweep_time = (finished - start)
            print(f"{self.recent_sweep_time}")
            # Stop continuous conversion for all ADCs
            self.nons.stop_adc()
            self.shunted.stop_adc()
            self.refer.stop_adc()
            self.tocsv(filename, data)

    def opv_loop_run(self):
        while self.running:
            file_path = self.generate_opv_file_name(self.directory)
            print(file_path)
            self.start_stop_weened(file_path)
            self.alive_flag.set()  # Update alive flag
            #print(f"ref: {self.ref_Voc}")
            #print(f"voc: {self.opv_Voc}")
            #print(f"isc: {self.opv_Isc}")
            #print(f"time: {self.recent_sweep_time}")
            time.sleep(0.1)

    def run(self):
        try:
            self.opv_loop_run()
        except Exception as e:
            self.alive_flag.clear()
            write_to_log_file('/home/logger/flight_logging/OPV_logs/OPV_log.txt', str(e))
            

