import RPi.GPIO as GPIO
import time
import csv
import os
from ADS_class import ADS_Sensors
from datetime import datetime

from gps_lib import gps_scan

class SensorDataLogger:
    def __init__(self):
        self.ads_sensors = ADS_Sensors()
        self.data_dir = "ADS_data"
        self.file_counter = 0
        self.entries_per_file = 1000
        self.current_entries = 0
        self.csv_file = None
        self.csv_writer = None

        # Create directory for storing CSV files
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        self.create_new_csv_file()

        # Define GPIO pins for interrupts
        self.MAG_TRICLOPS_INTERRUPT_PIN = 17  # GPIO pin for magnetometer and Triclops interrupt
        self.IMU_INTERRUPT_PIN = 18           # GPIO pin for IMU interrupt

        # GPIO setup
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.MAG_TRICLOPS_INTERRUPT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.IMU_INTERRUPT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # Setup interrupts
        GPIO.add_event_detect(self.MAG_TRICLOPS_INTERRUPT_PIN, GPIO.RISING, callback=self.mag_triclops_interrupt_handler, bouncetime=2)
        GPIO.add_event_detect(self.IMU_INTERRUPT_PIN, GPIO.RISING, callback=self.imu_interrupt_handler, bouncetime=2)

        self.gps_data = {
            'timestamp': '000000',  # HHMMSS format
            'latitude': 0,
            'longitude': 0,
            'ns_indicator': 'N',
            'ew_indicator': 'E',
            'ground_speed': 0,
            'altitude': 0,
            'snr': 0,
            'fix': 0
        }

    def create_new_csv_file(self):
        if self.csv_file:
            self.csv_file.close()
        timestamp = time.time()
        filename = os.path.join(self.data_dir, f"{timestamp}_ads_data_{self.file_counter}.csv")
        self.csv_file = open(filename, mode='w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow(['Time', 'MagX', 'MagY', 'MagZ', 'AccX', 'AccY', 'AccZ', 'GyroX', 'GyroY', 'GyroZ', 'Tri1', 'Tri2', 'Tri3', 'Latitude', 'Longitude', 'Altitude', 'GPS_Time'])
        self.file_counter += 1

    def mag_triclops_interrupt_handler(self, channel):
        self.ads_sensors.getMagReading()
        # Print sensor readings for Magnetometer and Triclops
        # print(f"Magnetometer X: {self.ads_sensors.magX}, Y: {self.ads_sensors.magY}, Z: {self.ads_sensors.magZ}")
        # print(f"Triclops 1: {self.ads_sensors.tri1}, 2: {self.ads_sensors.tri2}, 3: {self.ads_sensors.tri3}")

    def imu_interrupt_handler(self, channel):
        self.ads_sensors.getGyroReading()
        self.ads_sensors.getTriclopsReading()
        # Assuming a method to get GPS data
        # gps_data = self.ads_sensors.get_gps_data()  # Adjust this according to your actual method to get GPS data

        # Print sensor readings for IMU
        # print(f"Gyro X: {self.ads_sensors.gyroX}, Y: {self.ads_sensors.gyroY}, Z: {self.ads_sensors.gyroZ}")
        # print(f"Accelerometer X: {self.ads_sensors.accX}, Y: {self.ads_sensors.accY}, Z: {self.ads_sensors.accZ}")
        # print(f"Magnetometer X: {self.ads_sensors.magX}, Y: {self.ads_sensors.magY}, Z: {self.ads_sensors.magZ}")
        # print(f"Triclops 1: {self.ads_sensors.tri1}, 2: {self.ads_sensors.tri2}, 3: {self.ads_sensors.tri3}")
        # print(f"GPS Latitude: {gps_data['latitude']}, Longitude: {gps_data['longitude']}, Altitude: {gps_data['altitude']}, Time: {gps_data['time']}")

        # Write to CSV
        self.csv_writer.writerow([
            datetime.utcnow().isoformat(), 
            self.ads_sensors.magX, self.ads_sensors.magY, self.ads_sensors.magZ,
            self.ads_sensors.accX, self.ads_sensors.accY, self.ads_sensors.accZ,
            self.ads_sensors.gyroX, self.ads_sensors.gyroY, self.ads_sensors.gyroZ,
            self.ads_sensors.tri1, self.ads_sensors.tri2, self.ads_sensors.tri3,
            self.gps_data['latitude'], self.gps_data['longitude'], self.gps_data['altitude'], self.gps_data['timestamp']
        ])
        self.current_entries += 1

        # Check if we need a new file
        if self.current_entries >= self.entries_per_file:
            self.create_new_csv_file()
            self.current_entries = 0

    def run(self):
        self.ads_sensors.getMagReading() #Needed to initialize mag interrupts 
        while True:
            gps_scan(self.gps_data)
            time.sleep(0.2)

if __name__ == "__main__":
    logger = SensorDataLogger()
    logger.run()
