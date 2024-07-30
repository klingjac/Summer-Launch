import RPi.GPIO as GPIO
import time
from ADS_class import ADS_Sensors

# Initialize ADS_Sensors
ads_sensors = ADS_Sensors()

# Define GPIO pins for interrupts
MAG_TRICLOPS_INTERRUPT_PIN = 17  # GPIO pin for magnetometer and Triclops interrupt
IMU_INTERRUPT_PIN = 18           # GPIO pin for IMU interrupt

# GPIO setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(MAG_TRICLOPS_INTERRUPT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(IMU_INTERRUPT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def mag_triclops_interrupt_handler(channel):
    print("Magnetometer and Triclops Interrupt received!")
    ads_sensors.getMagReading()
    ads_sensors.getTriclopsReading()
    
    # Print sensor readings for Magnetometer and Triclops
    print(f"Magnetometer X: {ads_sensors.magX}, Y: {ads_sensors.magY}, Z: {ads_sensors.magZ}")
    print(f"Triclops 1: {ads_sensors.tri1}, 2: {ads_sensors.tri2}, 3: {ads_sensors.tri3}")

def imu_interrupt_handler(channel):
    print("IMU Interrupt received!")
    ads_sensors.getGyroReading()
    
    # Print sensor readings for IMU
    print(f"Gyro X: {ads_sensors.gyroX}, Y: {ads_sensors.gyroY}, Z: {ads_sensors.gyroZ}")

# Setup interrupts
GPIO.add_event_detect(MAG_TRICLOPS_INTERRUPT_PIN, GPIO.RISING, callback=mag_triclops_interrupt_handler, bouncetime=2)
GPIO.add_event_detect(IMU_INTERRUPT_PIN, GPIO.RISING, callback=imu_interrupt_handler, bouncetime=2)

ads_sensors.getMagReading()

try:
    print("Waiting for interrupts. Press Ctrl+C to exit.")
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("Exiting program.")

finally:
    GPIO.cleanup()
