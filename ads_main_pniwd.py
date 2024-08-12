import threading
import time
import RPi.GPIO as GPIO
import csv
import os
from ADS_class import ADS_Sensors
from datetime import datetime

def write_to_log_file(log_file, message):
    with open(log_file, 'a') as file:
        file.write(message + '\n')

class ADSSensorDataLogger:
    def __init__(self, rtc):
        self.ads_sensors = ADS_Sensors(rtc)
        self.data_dir = "ADS_data"
        self.file_counter = 0
        self.entries_per_file = 1000
        self.current_entries = 0
        self.csv_file = None
        self.csv_writer = None
        self.alive_flag = threading.Event()
        self.alive_flag.set()
        self.running = True
        self.imu_status = True
        self.pni_status = True
        self.RTC = rtc

        # GPIO setup and initialization
        self.setup_gpio()
        self.create_new_csv_file()

    def setup_gpio(self):
        # Define GPIO pins for interrupts
        self.MAG_TRICLOPS_INTERRUPT_PIN = 18  # GPIO pin for magnetometer and Triclops interrupt
        self.IMU_INTERRUPT_PIN = 4            # GPIO pin for IMU interrupt

        # GPIO setup
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.MAG_TRICLOPS_INTERRUPT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.IMU_INTERRUPT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # Setup interrupts
        GPIO.add_event_detect(self.MAG_TRICLOPS_INTERRUPT_PIN, GPIO.RISING, callback=self.safe_mag_interrupt_handler, bouncetime=1)
        GPIO.add_event_detect(self.IMU_INTERRUPT_PIN, GPIO.RISING, callback=self.safe_imu_triclops_interrupt_handler, bouncetime=1)

    def cleanup_gpio(self):
        GPIO.remove_event_detect(self.MAG_TRICLOPS_INTERRUPT_PIN)
        GPIO.remove_event_detect(self.IMU_INTERRUPT_PIN)
        GPIO.cleanup()

    def create_new_csv_file(self):
        if self.csv_file:
            self.csv_file.close()
        timestamp = self.RTC.getTime()
        filename = os.path.join(self.data_dir, f"{timestamp}_ads_data_{self.file_counter}.csv")
        self.csv_file = open(filename, mode='w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow([timestamp])
        self.csv_writer.writerow(['MagX', 'MagY', 'MagZ', 'AccX', 'AccY', 'AccZ', 'GyroX', 'GyroY', 'GyroZ', 'Tri1', 'Tri2', 'Tri3', 'Latitude', 'Longitude', 'Altitude', 'GPS_Time'])
        self.file_counter += 1

    def safe_mag_interrupt_handler(self, channel):
        self.pni_status = True
        try:
            self.mag_interrupt_handler(channel)
        except Exception as e:
            self.alive_flag.clear()
            print(f"Exception in mag_interrupt_handler: {e}")

    def mag_interrupt_handler(self, channel):
        self.ads_sensors.getMagReading()

    def safe_imu_triclops_interrupt_handler(self, channel):
        self.imu_status = True
        try:
            self.imu_triclops_interrupt_handler(channel)
        except Exception as e:
            self.alive_flag.clear()
            print(f"Exception in imu_triclops_interrupt_handler: {e}")

    def imu_triclops_interrupt_handler(self, channel):
        self.ads_sensors.getGyroReading()
        self.ads_sensors.getTriclopsReading()

        # Write to CSV
        try: 
            self.csv_writer.writerow([
                self.ads_sensors.magX, self.ads_sensors.magY, self.ads_sensors.magZ,
                self.ads_sensors.accX, self.ads_sensors.accY, self.ads_sensors.accZ,
                self.ads_sensors.gyroX, self.ads_sensors.gyroY, self.ads_sensors.gyroZ,
                self.ads_sensors.tri1, self.ads_sensors.tri2, self.ads_sensors.tri3,
                self.ads_sensors.GPS.gps_data['latitude'], self.ads_sensors.GPS.gps_data['longitude'], self.ads_sensors.GPS.gps_data['altitude'], self.ads_sensors.GPS.gps_data['timestamp']
            ])
            self.current_entries += 1
        except:
            return

        # Check if we need a new file
        if self.current_entries >= self.entries_per_file:
            self.create_new_csv_file()
            self.current_entries = 0

    def run(self):
        try:
            self.ads_sensors.getMagReading()
            while self.running:
                #self.alive_flag.set()  # Update alive flag
                if self.imu_status and self.pni_status:
                    self.alive_flag.set()
                self.imu_status = False
                self.pni_status = False
                time.sleep(0.2)
        except Exception as e:
            self.alive_flag.clear()
            write_to_log_file('/home/logger/flight_logging/ADS_logs/ADS_log.txt', str(e))
        finally:
            self.cleanup_gpio() #Necessary to prevent dumb stuff from happening
    
    def stop(self):
        self.running = False
