import lib.pni_rm3100
import time
import threading
import math
from datetime import datetime, timezone
import csv
import os

from lib.icm20948_lib import ICM20948
from lib.icm20948_lib import I2C_ADDR_ALT
from lib.icm20948_lib import AK09916_HXL
from lib.icm20948_lib import AK09916_CNTL2
from lib.icm20948_lib import ICM20948_ACCEL_XOUT_H

from lib.AD7994 import AD7994 
from lib.pni_rm3100 import PniRm3100

from lib.gps_lib import GPSScanner

class ADS_Sensors():

    #Sensor Objects
    magnetometer = None
    imu_gyro = None
    triclops = None

    mag_addr = 0x23

    #Private State Variables For ADS Estimation
    gyroX = 0
    gyroY = 0
    gyroZ = 0

    accX = 0
    accY = 0
    accZ = 0

    magX = 0
    magY = 0
    magZ = 0

    tri1 = 0
    tri2 = 0
    tri3 = 0


    latitude = 42.75
    longitude = -84.99
    altitude = 0.3
    gps_time = 0

    csv_entries = 0

    filecsv = None
    filelog = None


    ADS_Header = ['Time', 'MagX', 'MagY', 'MagZ', 'GyroX', 'GyroY', 'GyroZ', 'Tri11', 'Tri12', 'Tri13']

    

    def __init__(self):
        #Initialize gyro as +- 8g and +- 2000 dps
        self.imu_gyro = ICM20948(i2c_addr=I2C_ADDR_ALT, i2c_bus=2)
        self.imu_gyro.set_accelerometer_full_scale(4) #Accelerometer scale range
        self.imu_gyro.set_gyro_full_scale(1000) #Gyro scale range

        self.imu_gyro.set_accelerometer_sample_rate(75) #accelerometer rate
        self.imu_gyro.set_gyro_sample_rate(75) #gyro rate
        
        #Initialize rm3100 mag, use sampling rate of 37hz by default
        self.magnetometer = PniRm3100()
        self.magnetometer.assign_device_addr(self.mag_addr)

        self.magnetometer.print_status_statements = False
        self.magnetometer.print_debug_statements = False

        self.magnetometer.assign_xyz_ccr(x_ccr_in=self.magnetometer.CcrRegister.CCR_DEFAULT, 
                                     y_ccr_in=self.magnetometer.CcrRegister.CCR_DEFAULT, 
                                     z_ccr_in=self.magnetometer.CcrRegister.CCR_DEFAULT)
    
        self.magnetometer.assign_tmrc(self.magnetometer.TmrcRegister.TMRC_75HZ) #Initialized to 75 Hz
        self.magnetometer.write_ccr()
        self.magnetometer.write_config()

        self.triclops = AD7994(address = 0x24)

        self.sun_ref = 3 #For later Triclops Conversion
        self.MaxCounts = 1023

        self.GPS = GPSScanner()

        self.gps_thread = threading.Thread(target=self.GPS.gps_scan)
        self.gps_thread.start()


    def getTriclopsReading(self):
        data = self.triclops.get_data() 
        
        byte_convert = [point * self.sun_ref/self.MaxCounts for point in data]
        self.tri1 = byte_convert[0]
        self.tri2 = byte_convert[1]
        self.tri3 = byte_convert[2]


    def getMagReading(self):
        readings = self.magnetometer.read_meas() 

        # Relative magnetometer readings
        magX = readings[0]
        magY = readings[1]
        magZ = readings[2]

        # MC10 Orientation mag
        self.magX = magY
        self.magY = magX
        self.magZ = -magZ

    def getGyroReading(self):
        #data = self.imu.read_bytes(ICM20948_ACCEL_XOUT_H + 6, 12) #Return the raw gyro readings, each is a raw 2 bytes
        ax, ay, az, gx, gy, gz = self.imu_gyro.read_accelerometer_gyro_data()

        # MC10 relative gyro
        self.gyroX = gy
        self.gyroY = gx
        self.gyroZ = gz

        self.accX = ax
        self.accY = ay
        self.accZ = az


    

    