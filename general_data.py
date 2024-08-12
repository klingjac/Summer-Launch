from lib.ads7828 import ADS7828  # Adjust the import based on your actual module
import psutil
import smbus2
import bme680
from lib.tmp102 import TMP102  # Import the provided TMP102 library
from lib.eddy_eps import EddyEps
import threading
import csv
import time
import os

def write_to_log_file(log_file, message):
    with open(log_file, 'a') as file:
        file.write(message + '\n')

class Status_Data:
    def __init__(self, rtc, i2c_bus_number=2, tmp102_address=0x4B, bme680_address=0x77):
        self.eps = EddyEps(smbus_num=2)
        self.i2c_bus = smbus2.SMBus(2)
        self.tmp102_address = tmp102_address
        self.bme680_address = bme680_address
        
        self.VbattRaw = 0
        self.IbattRaw = 0
        self.Vbatt = 0
        self.Ibatt = 0
        self.V3v3 = 0
        self.I3v3 = 0
        self.V5v0 = 0
        self.I5v0 = 0
        self.T3v3 = 0
        self.T5v0 = 0
        self.free_memory = 0
        self.free_disk_space = 0
        self.cpu_temp = 0
        self.tmp102_temp = 0
        self.bme680_temp = 0
        self.bme680_pressure = 0
        self.running = True
        self.RTC = rtc

        # Initialize TMP102 sensor
        self.tmp102_sensor = TMP102(units='C', address=self.tmp102_address, busnum=2)
        
        # Initialize BME680 sensor with the specified I2C bus
        self.bme680_sensor = self.initialize_bme680()

        self.alive_flag = threading.Event()
        self.alive_flag.set()

        # Create directory for storing CSV files
        self.data_dir = "status_data"
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        self.csv_file = None
        self.csv_writer = None

    def initialize_bme680(self):
        # Temporarily set the bus for BME680 initialization
        original_bus = smbus2.SMBus(2)
        try:
            # Attempt to initialize on the specified bus
            return bme680.BME680(i2c_addr=self.bme680_address, i2c_device=self.i2c_bus)
        finally:
            original_bus.close()

    def create_new_csv_file(self):
        if self.csv_file:
            self.csv_file.close()
        timestamp = self.RTC.getTime()
        filename = os.path.join(self.data_dir, f"{timestamp}_status_data.csv")
        self.csv_file = open(filename, mode='w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow(['Time', 'VbattRaw', 'IbattRaw', 'Vbatt', 'Ibatt', 'V3v3', 'I3v3', 'V5v0', 'I5v0', 'T3v3', 'T5v0', 'Free Memory', 'Free Disk Space', 'CPU Temperature', 'TMP102 Temperature', 'BME680 Temperature', 'BME680 Pressure'])

    def update_eps_values(self):
        self.VbattRaw = self.eps.get_voltage_vbatt_raw() #or 0
        self.IbattRaw = self.eps.get_current_vbatt_raw() #or 0
        self.V3v3 = self.eps.get_voltage_3v3() #or 0
        self.I3v3 = self.eps.get_current_3v3() #or 0
        self.V5v0 = self.eps.get_voltage_5v0() #or 0
        self.I5v0 = self.eps.get_current_5v0() #or 0
        self.Vbatt = self.eps.get_voltage_vbatt() #or 0
        self.Ibatt = self.eps.get_current_vbatt() #or 0
        self.T3v3 = self.eps.get_temp_3v3_reg() #or 0
        self.T5v0 = self.eps.get_temp_5v0_reg() #or 0

    def update_system_values(self):
        self.free_memory = psutil.virtual_memory().available / (1024 * 1024)  # Convert bytes to MB
        self.free_disk_space = psutil.disk_usage('/').free / (1024 * 1024)  # Convert bytes to MB
        self.cpu_temp = self.get_cpu_temp()

    def get_cpu_temp(self):
        try:
            temperature = float(open("/sys/class/thermal/thermal_zone0/temp").read()) / 1000.0
            return temperature
        except Exception as e:
            print(f"Error getting CPU temperature: {e}")
            return 0

    def read_tmp102_temp(self):
        try:
            self.tmp102_temp = self.tmp102_sensor.readTemperature()
        except Exception as e:
            print(f"Error reading TMP102 temperature: {e}")
            self.tmp102_temp = 0

    def read_bme680(self):
        try:
            if self.bme680_sensor.get_sensor_data():
                self.bme680_temp = self.bme680_sensor.data.temperature
                self.bme680_pressure = self.bme680_sensor.data.pressure
        except Exception as e:
            print(f"Error reading BME680 sensor: {e}")
            self.bme680_temp = 0
            self.bme680_pressure = 0

    def update_all_values(self):
        self.update_eps_values()
        self.update_system_values()
        self.read_tmp102_temp()
        self.read_bme680()

    def log_status(self):
        timestamp = self.RTC.getTime()
        self.csv_writer.writerow([
            timestamp,
            self.VbattRaw, self.IbattRaw, self.Vbatt, self.Ibatt, 
            self.V3v3, self.I3v3, self.V5v0, self.I5v0, 
            self.T3v3, self.T5v0, 
            self.free_memory, self.free_disk_space, self.cpu_temp, 
            self.tmp102_temp, self.bme680_temp, self.bme680_pressure
        ])
        self.csv_file.flush()  # Ensure data is written to the file
        

    def run(self):
        self.create_new_csv_file()
        while self.running:
            self.alive_flag.is_set()
            self.update_all_values()
            self.log_status()
            time.sleep(5)

    def stop(self):
        self.alive_flag.clear()
        self.running = False
        if self.csv_file:
            self.csv_file.close()

# Example usage
if __name__ == "__main__":
    eps = ADS7828()  # Replace with your actual EPS object initialization
    status = Status_Data(i2c_bus_number=2)  # Specify the I2C bus number here
    status.run()
