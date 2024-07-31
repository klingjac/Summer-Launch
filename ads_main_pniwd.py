import multiprocessing
import time
import RPi.GPIO as GPIO
import csv
import os
from ADS_class import ADS_Sensors
from datetime import datetime

class ADSSensorDataLogger:
    def __init__(self, heartbeat):
        self.ads_sensors = ADS_Sensors()
        self.data_dir = "ADS_data"
        self.file_counter = 0
        self.entries_per_file = 1000
        self.current_entries = 0
        self.csv_file = None
        self.csv_writer = None
        self.pni_interrupt_flag = False
        self.running = True
        self.heartbeat = heartbeat

        # Create directory for storing CSV files
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        self.create_new_csv_file()

        # Define GPIO pins for interrupts
        self.MAG_TRICLOPS_INTERRUPT_PIN = 18  # GPIO pin for magnetometer and Triclops interrupt
        self.IMU_INTERRUPT_PIN = 4           # GPIO pin for IMU interrupt

        # GPIO setup
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.MAG_TRICLOPS_INTERRUPT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.IMU_INTERRUPT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # Setup interrupts
        GPIO.add_event_detect(self.MAG_TRICLOPS_INTERRUPT_PIN, GPIO.RISING, callback=self.mag_triclops_interrupt_handler, bouncetime=1)
        GPIO.add_event_detect(self.IMU_INTERRUPT_PIN, GPIO.RISING, callback=self.imu_interrupt_handler, bouncetime=1)

        self.ads_sensors.getMagReading()

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
        self.pni_interrupt_flag = True

    def imu_interrupt_handler(self, channel):
        self.ads_sensors.getGyroReading()
        self.ads_sensors.getTriclopsReading()

        # Write to CSV
        self.csv_writer.writerow([
            datetime.utcnow().isoformat(),
            self.ads_sensors.magX, self.ads_sensors.magY, self.ads_sensors.magZ,
            self.ads_sensors.accX, self.ads_sensors.accY, self.ads_sensors.accZ,
            self.ads_sensors.gyroX, self.ads_sensors.gyroY, self.ads_sensors.gyroZ,
            self.ads_sensors.tri1, self.ads_sensors.tri2, self.ads_sensors.tri3,
            self.ads_sensors.GPS.gps_data['latitude'], self.ads_sensors.GPS.gps_data['longitude'], self.ads_sensors.GPS.gps_data['altitude'], self.ads_sensors.GPS.gps_data['timestamp']
        ])
        self.current_entries += 1

        # Check if we need a new file
        if self.current_entries >= self.entries_per_file:
            self.create_new_csv_file()
            self.current_entries = 0

    def interrupt_tracker(self):
        while self.running:
            if not self.pni_interrupt_flag:
                print("No interrupt in the past second, manually triggering a read")
                self.ads_sensors.getMagReading()
            self.pni_interrupt_flag = False
            self.heartbeat.value = True  # Update heartbeat
            time.sleep(1)

    def run(self):
        self.ads_sensors.getMagReading()
        while self.running:
            self.heartbeat.value = True  # Update heartbeat
            time.sleep(0.2)

def run_ads_logger(heartbeat):
    logger = ADSSensorDataLogger(heartbeat)
    logger.run()

if __name__ == "__main__":
    heartbeat = create_shared_heartbeat()
    run_ads_logger(heartbeat)
