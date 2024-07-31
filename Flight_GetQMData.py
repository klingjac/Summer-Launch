
"""
Based Off Of Run_Quad-Mag.py

TASKS ONCE UPLOADED TO FCPU:
CTRL+F "data_storage/" and replace it with some QM-related folder heading throughout the entire file.
"""



import serial
import sys
from sys import byteorder
import data_processing_lib.data_commands_lib as dcl
import csv
import threading
from datetime import datetime
import time

#import keyboard
#import numpy as np
#Below is in get_mag_config() function
#Open Serial port -> ser = openSerialPort()
#Default command begins with b'\x01'
#Default Cycle counts is 800 which is b'\x03\x20' -> 200 is b'\x00\xC8'
#Default Sample rate is 37 Hz which is b'\x04' -> Optional Sample rate is 75 Hz which is b'\x03'
#Default Oversamples is 1 which is  b'\x01'
#Combined command for all default values above is command = b'\x01\x03\x20\x04\x01\x00\x00\x00\x00\x00'
#Need to write this command to serial port -> ser.write(command)

#Below is in continuous_measurement() function
#Begin with command for continous measurement which is command = b'\x06'
#Removing user-defined sample rate question mark? command = command + b'\x00\x00'
#enabling all mags is mag = 0b1111 -> converting to \x -> b'\x0f'
#Asks for how long to take measurements -> probably for 30 seconds but testing would be 10 seconds
# 10 seconds == b'\x00\x00\x00\x00\x00\n' ;;; 30 seconds = b'\x00\x00\x00\x00\x00\x1e'
#Overall 10 second command would be command = b'\x06\x00\x00\x0f\x00\x00\x00\x00\x00\n' 
#Overall 30 second command would be command = b'\x06\x00\x00\x0f\x00\x00\x00\x00\x00\x1e'
#txt file must be opened before writing to it
#For just using the magnetometers -> txt.write("Mag Cycle Count, Mag Number of Oversamples (readings are raw)\n"))
#Next row would be txt.write("Packet Flag, System Time (sec), B1-X , B1-Y, B1-Z, B2-X, B2-Y, B2-Z, B3-X, B3-Y, B3-Z, B4-X, B4-Y, B4-Z\n")
#Write the command above to serial -> serial.write(command)

class QuadMag:
    # TODO: Put any necessary member variables here
    #frequency: float # <-- Example
    SampleRate: float
    CollectionTime: float
    Mode: str
    DataLength: int
    CycleCount: int
    OverSamples: int
    IGRF: int
    filename: str
    mag_readings: list
    magDataLock: threading.Lock
    magDataCV: threading.Condition

    def __init__(self, _magDataArray=[], _magDataLock=threading.Lock(), _magDataCV=None, _RTC=None):
        # Do any sensor setup you need, use default values
        # For any configurable values have member variables to store state and define methods to change the state
        #frequency = 10
        self.SampleRate = 37 #Hz -> Default rate
        self.CollectionTime = 300 #seconds -> Default collection time
        self.Mode = "Default" #Default mode -> 200 cycle counts, 1 over sample, 37 Hz sample rate
        self.DataLength = 50 #Default data list length
        self.CycleCount = 200
        self.OverSamples = 1
        self.IGRF = 40 #Set to desired IGRF based on location
        self.filename = "testing_"
        self.mag_readings = _magDataArray
        self.magDataLock = _magDataLock
        if(_magDataCV == None): self.magDataCV = threading.Condition(self.magDataLock)
        else: self.magDataCV = _magDataCV
        self.RTC = _RTC
    
    def GetQuadMagDiagnostic(self):
        #Opening Serial Port
        ser = self.OpenSerialPort()
        #Configuring the Magnetometers
        self.Config_QuadMag(ser)
        file_path = 'data_storage/'
        file_csv = file_path + self.filename + '_diagnostics.csv'
        with open(file_csv,mode="w") as csv_file:
            csvwriter = csv.writer(csv_file)
            #This is initializing command for serial port -> b'\x06' = continuous measurement mode
            command = b'\x06'
            command = command + b'\x00\x00' #artifact of removing user defined sample rate/on-board averaging
            mags_enabled = 0b1111 #All mags are enabled
            command = command + (mags_enabled).to_bytes(1, byteorder='big') #Add Mags into command
            command = command + (int(self.CollectionTime)).to_bytes(6, byteorder='big') #Add collection time into command
            #Adding file headers and writing to csv
            csvwriter.writerow(["Packet Flag","System Time (sec)","B1-X","B1-Y","B1-Z","B2-X","B2-Y","B2-Z","B3-X","B3-Y","B3-Z","B4-X","B4-Y","B4-Z","Temp"])
            #print('Command: ',command)
            ser.write(command)
            #Taking measurements and verifying that data is collected properly
            total_measurements = 0
            expected_measurements = (int(self.CollectionTime)) * int(self.SampleRate)
            invalid_packet_count = 0
            invalid_packet_threshold = int(float(expected_measurements) * 0.1)  #10% of expected measurements
            print_threshold = int(float(expected_measurements) * 0.05) #5% of expected measurements
            return_string = ""
            while 1:
                
                returned_bytes_string = dcl.get_response_helper(ser)
                #print('returned bytes: ',returned_bytes_string)
                # Stops the python program from attempting invalid string
                # operations....
                if (returned_bytes_string == '') or (returned_bytes_string[1] == "COMPLETE"):
                    #return_string = "\nContinuous measurement completed successfully!"
                    #break
                    pass
                elif returned_bytes_string[1] == '':
                    return_string = "\nContinuous measurement completed successfully!"
                    break
                elif invalid_packet_count > invalid_packet_threshold:
                    return "\nToo many invalid packets received, continuous measurement did not complete successfully!"
                elif len(returned_bytes_string[1]) > 0:
                    total_measurements = total_measurements + 1
                    raw_data = returned_bytes_string[1].split(",")
                    processed_data = []
                    for val in range(len(raw_data)):
                        if val == 0:
                            processed = int(raw_data[val]).to_bytes(1,"big")
                            processed_data.append(processed)
                        elif val == 1:
                            byte = int(float(raw_data[val])*1000)
                            processed = byte.to_bytes(8,"big")
                            processed_data.append(processed)
                        elif raw_data[val] == '':
                            pass
                        elif (val >=2) and (val<=13):
                            processed = float(raw_data[val])/(0.3671*self.CycleCount + 1.5)/self.OverSamples
                            processed_conv = processed*1000
                            processed_byte = int(processed_conv).to_bytes(4,"big",signed=True)
                            processed_data.append(processed_byte) #Ground station must divide by 1000 to get real value
                        elif val == 20:
                            #Converting from bytes to temp -> tempVoltage == mV
                            tempVoltage = (int(raw_data[val]) * 2500) >> 12
                            #Take mV value and convert to temperature in Celsius
                            processed = (tempVoltage - 500) / 10.0
                            #Converting back to bytes -> divide by 10 for conversion function
                            processed = int(raw_data[val]*10).to_bytes(4,"big",signed=True)
                            processed_data.append(processed)
                    csvwriter.writerow(processed_data)
                    #write_file_raw.write(str(processed_data) + "\n")
                else:
                    invalid_packet_count = invalid_packet_count + 1

            print("\n******Finished a continuous measurement******\n")
            print("\nExpected Measurements: " + str(expected_measurements))
            print("\nMissing Measurements: " + str(expected_measurements - total_measurements) + "\n")
            print("\nInvalid Packets Received: " + str(invalid_packet_count) + "\n")

        #Close Port
        ser.close()
        return return_string

    def getReading_raw(self):
        """
        Get one set of readings from the sensor
        This should return in bytes the converted values to be sent directly to the ground
        I.e. you should get your value, then apply the conversion function comms has defined
            then change it to a bytes object and return
        This should get all readings from your subsystem, unless you are defining multiple sensors for your subsystem
        """
        reading = []
        #Open Serial port /dev/ttyUSB0
        ser = self.OpenSerialPort()
        #Configure Quad-Mag
        updatedconfig = self.Config_QuadMag(ser)
        #print(updatedconfig)
        #This is initializing command for serial port -> b'\x06' = continuous measurement mode
        command = b'\x06'
        command = command + b'\x00\x00' #artifact of removing user defined sample rate/on-board averaging
        mags_enabled = 0b1111 #All mags are enabled
        command = command + (mags_enabled).to_bytes(1, byteorder='big') #Add Mags into command
        command = command + (int(self.CollectionTime)).to_bytes(6, byteorder='big') #Add collection time into command
        #print(command)
        ser.write(command)
        #Taking measurements and verifying that data is collected properly
        total_measurements = 0
        expected_measurements = (int(self.CollectionTime)) * int(self.SampleRate)
        invalid_packet_count = 0
        invalid_packet_threshold = int(float(expected_measurements) * 0.1)  #10% of expected measurements
        print_threshold = int(float(expected_measurements) * 0.05) #5% of expected measurements
        return_string = ""
        while 1:
            
            returned_bytes_string = dcl.get_response_helper(ser)
            #print('returned bytes: ',returned_bytes_string)
            # Stops the python program from attempting invalid string
            # operations....
            if (returned_bytes_string == '') or (returned_bytes_string[1] == "COMPLETE"):
                #return_string = "\nContinuous measurement completed successfully!"
                #break
                pass
            elif returned_bytes_string[0] == '':
                return_string = "\nContinuous measurement completed successfully!"
                break
            elif invalid_packet_count > invalid_packet_threshold:
                return "\nToo many invalid packets received, continuous measurement did not complete successfully!"
            elif len(returned_bytes_string[1]) > 0:
                total_measurements = total_measurements + 1
                #write_file_raw.write(returned_bytes_string[1] + "\n")
                if len(reading) <= self.DataLength:
                    reading.append(returned_bytes_string[1])
                elif len(reading) > self.DataLength:
                    data = reading.pop()
                    reading.insert(0, returned_bytes_string[1])
                    return data
            else:
                invalid_packet_count = invalid_packet_count + 1
        
        # print("\n******Finished a continuous measurement******\n")
        # print("\nExpected Measurements: " + str(expected_measurements))
        # print("\nMissing Measurements: " + str(expected_measurements - total_measurements) + "\n")
        # print("\nInvalid Packets Received: " + str(invalid_packet_count) + "\n")
        #Close Port
        ser.close()
    
    #Returns a single data point in a 2 elmement list [raw_data,processed_data]
    def getReading(self):
        """
        Get one set of readings from the sensor
        This should return in bytes the converted values to be sent directly to the ground
        I.e. you should get your value, then apply the conversion function comms has defined
            then change it to a bytes object and return
        This should get all readings from your subsystem, unless you are defining multiple sensors for your subsystem
        """
        raw_data = self.getReading_raw()
        print(raw_data)
        raw_data = raw_data.split(',')
        processed_data = []
        for val in range(len(raw_data)):
            if (val == 0) or (val == 1):
                processed_data.append(raw_data[val])
            elif raw_data[val] == '':
                pass
            else:
                processed_data.append(float(raw_data[val])/75)
        data = [raw_data,processed_data]
        return data

    #Main data collection function that gets data from all 4 QM's
    def CollectData(self, flag):

        #Open Serial Port
        ser = self.OpenSerialPort()
        #Config Quadmag
        self.Config_QuadMag(ser)
        #Get filepath
        file_path = 'data_storage/'

        #TODO: maybe uncomment
        if self.filename == "testing_":
            try: self.filename = str(self.RTC.getTime())
            except: self.filename = str(time.time())
            file_csv = file_path + self.filename + '_collectdata.csv'
        else:
            file_csv = file_path + self.filename + '.csv'
        print("Printing to " + file_csv + "\n")
        
        
        #Open CSV file
        with open(file_csv,mode="w") as csv_file:
            csvwriter = csv.writer(csv_file)
            #This is initializing command for serial port -> b'\x06' = continuous measurement mode
            command = b'\x06'
            command = command + b'\x00\x00' #artifact of removing user defined sample rate/on-board averaging
            mags_enabled = 0b1111 #All mags are enabled
            command = command + (mags_enabled).to_bytes(1, byteorder='big') #Add Mags into command
            command = command + (int(self.CollectionTime)).to_bytes(6, byteorder='big') #Add collection time into command
            #Adding file headers and writing to csv
            csvwriter.writerow(["Packet Flag","System Time (sec)","B1-X","B1-Y","B1-Z","B2-X","B2-Y","B2-Z","B3-X","B3-Y","B3-Z","B4-X","B4-Y","B4-Z","Temp"])
            #print('Command: ',command)
            #Write command to serial
            ser.write(command)
            #Taking measurements and verifying that data is collected properly
            total_measurements = 0
            expected_measurements = (int(self.CollectionTime)) * int(self.SampleRate)
            invalid_packet_count = 0
            invalid_packet_threshold = int(float(expected_measurements) * 0.1)  #10% of expected measurements
            print_threshold = int(float(expected_measurements) * 0.05) #5% of expected measurements
            return_string = ""
            while 1:
                #Get data from QM
                returned_bytes_string = dcl.get_response_helper(ser)
                try:
                    rtc_time = self.RTC.getTime()
                except:
                    rtc_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                #print('returned bytes: ',returned_bytes_string)
                # Stops the python program from attempting invalid string
                # operations....
                if (returned_bytes_string == '') or (returned_bytes_string[1] == "COMPLETE") or (returned_bytes_string == None):
                    #return_string = "\nContinuous measurement completed successfully!"
                    #break
                    pass
                elif returned_bytes_string[1] == '':
                    return_string = "\nContinuous measurement completed successfully!"
                    break
                elif invalid_packet_count > invalid_packet_threshold:
                    return "\nToo many invalid packets received, continuous measurement did not complete successfully!"
                elif len(returned_bytes_string[1]) > 0:
                    total_measurements = total_measurements + 1
                    raw_data = returned_bytes_string[1].split(",")
                    processed_data = []
                    for val in range(len(raw_data)):
                        if val == 0:
                            processed = int(raw_data[val]).to_bytes(1,"big")
                            processed_data.append(processed)
                        elif val == 1:
                            #byte = int(float(raw_data[val])*1000)
                            processed_data.append(rtc_time)
                        elif raw_data[val] == '':
                            pass
                        elif (val >=2) and (val<=13):
                            processed = float(raw_data[val])/(0.3671*self.CycleCount + 1.5)/self.OverSamples
                            if flag == 1:
                                processed_conv = processed*1000
                                #processed_byte = int(processed_conv).to_bytes(4,"big",signed=True)
                                processed_byte = int(processed_conv).to_bytes(4,"big",signed=True)
                                #Ground station must divide by 1000 to get real value
                            else:
                                processed_byte = processed
                            processed_data.append(processed_byte) 
                        elif val == 20:
                            #Converting from bytes to temp -> tempVoltage == mV
                            tempVoltage = (int(raw_data[val]) * 2500) >> 12
                            #Take mV value and convert to temperature in Kelvin
                            processed = (tempVoltage - 500) / 10.0
                            if flag == 1:
                                #Converting back to bytes -> divide by 10 for conversion function
                                processed = int(processed*10).to_bytes(4,"big",signed=True)
                            processed_data.append(processed)
                    self.magDataLock.acquire()
                    self.mag_readings.append(processed_data[2:])
                    self.magDataCV.notify()
                    self.magDataLock.release()
                    csvwriter.writerow(processed_data)
                    #write_file_raw.write(str(processed_data) + "\n")
                else:
                    invalid_packet_count = invalid_packet_count + 1

            print("\n******Finished a continuous measurement******\n")
            print("\nExpected Measurements: " + str(expected_measurements))
            print("\nMissing Measurements: " + str(expected_measurements - total_measurements) + "\n")
            print("\nInvalid Packets Received: " + str(invalid_packet_count) + "\n")

        #Close Port
        ser.close()
        return return_string
    
    #Collect data by taking average of all Mags -> AvgX, AxgY, AvgZ
    def CollectAvgData(self):
        #Open Serial Port
        ser = self.OpenSerialPort()
        #Config Quadmag
        self.Config_QuadMag(ser)
        #Get filepath
        file_path = 'data_storage/'
        file_csv = file_path + self.filename + '_avgdata.csv'
        #Open CSV file
        with open(file_csv,mode="w") as csv_file:
            csvwriter = csv.writer(csv_file)
            #This is initializing command for serial port -> b'\x06' = continuous measurement mode
            command = b'\x06'
            command = command + b'\x00\x00' #artifact of removing user defined sample rate/on-board averaging
            mags_enabled = 0b1111 #All mags are enabled
            command = command + (mags_enabled).to_bytes(1, byteorder='big') #Add Mags into command
            command = command + (int(self.CollectionTime)).to_bytes(6, byteorder='big') #Add collection time into command
            #Adding file headers and writing to csv
            csvwriter.writerow(["Packet Flag","System Time (sec)","AvgX","AvgY","AvgZ"])
            #print('Command: ',command)
            #Write command to serial
            ser.write(command)
            #Taking measurements and verifying that data is collected properly
            total_measurements = 0
            expected_measurements = (int(self.CollectionTime)) * int(self.SampleRate)
            invalid_packet_count = 0
            invalid_packet_threshold = int(float(expected_measurements) * 0.1)  #10% of expected measurements
            print_threshold = int(float(expected_measurements) * 0.05) #5% of expected measurements
            return_string = ""
            while 1:
                #Get data from QM
                returned_bytes_string = dcl.get_response_helper(ser)
                rtc_time = self.RTC.getTime()
                #print('returned bytes: ',returned_bytes_string)
                # Stops the python program from attempting invalid string
                # operations....
                if (returned_bytes_string == '') or (returned_bytes_string[1] == "COMPLETE"):
                    #return_string = "\nContinuous measurement completed successfully!"
                    #break
                    pass
                elif returned_bytes_string[1] == '':
                    return_string = "\nContinuous measurement completed successfully!"
                    break
                elif invalid_packet_count > invalid_packet_threshold:
                    return "\nToo many invalid packets received, continuous measurement did not complete successfully!"
                elif len(returned_bytes_string[1]) > 0:
                    total_measurements = total_measurements + 1
                    raw_data = returned_bytes_string[1].split(",")
                    x_avg = 0
                    y_avg = 0
                    z_avg = 0
                    avg = []
                    for val in range(len(raw_data)):
                        if (val == 0):
                            avg.append(raw_data[val])
                        elif (val == 1):
                            #avg.append(raw_data[val])
                            avg.append(rtc_time)
                        elif raw_data[val] == '':
                            pass
                        elif (val==2) or (val==5) or (val==8) or (val==11):
                            processed = int(raw_data[val])/(0.3671*self.CycleCount + 1.5)/self.OverSamples
                            x_avg += processed
                        elif (val==3) or (val==6) or (val==9) or (val==12):
                            processed = int(raw_data[val])/(0.3671*self.CycleCount + 1.5)/self.OverSamples
                            y_avg += processed
                        elif (val==4) or (val==7) or (val==10) or (val==13):
                            processed = int(raw_data[val])/(0.3671*self.CycleCount + 1.5)/self.OverSamples
                            z_avg += processed
                    avg.append(str(int((x_avg/4)*100)/100))
                    avg.append(str(int((y_avg/4)*100)/100))
                    avg.append(str(int((z_avg/4)*100)/100))
                    csvwriter.writerow(avg)
                else:
                    invalid_packet_count = invalid_packet_count + 1

            print("\n******Finished a continuous measurement******\n")
            print("\nExpected Measurements: " + str(expected_measurements))
            print("\nMissing Measurements: " + str(expected_measurements - total_measurements) + "\n")
            print("\nInvalid Packets Received: " + str(invalid_packet_count) + "\n")

        #Close Port
        ser.close()
        return return_string
    
    #Calibration function that assumes data has already been taken and saved to a CSV file
    def CalibrateQuadMag(self):
        #file directory to data
        file_path = 'data_storage/'
        #CSV file to calibrate
        csv_file = file_path + self.filename + '_avgdata.csv'
        #Get Mag params -> returns index then value pair or list of a list of a single value
        # eg. [[3][4][5][6][7]]
        mag_parameters = magCalParameter.main(csv_file, self.IGRF)
        #Condensing the list of a list to a singular list
        x = []
        for i in range(len(mag_parameters)):
            x.append(mag_parameters[i][0])
        #Return the mag cal parameters
        return x
        #Code below takes the parameters and adjusts the data to calibrated data
        # Read the csv_file
        #read_data = pd.read_csv(csv_file)
        #Get the AvgX, AvgY, and AvgZ columns from csv_file
        #initial_x = np.array(read_data["AvgX"])
        #initial_y = np.array(read_data["AvgY"])
        #initial_z = np.array(read_data["AvgZ"])
        #Call the sensor correction function
        #x_corrected, y_corrected, z_corrected = correctSensor_v6(x, initial_x, initial_y, initial_z)
        #x_corrected_bytes = []
        #y_corrected_bytes = []
        #z_corrected_bytes = []
        #for i in range(len(x_corrected)):
            #x_corrected_bytes.append(int(x_corrected[i]*100).to_bytes(4,"big",signed=True))
            #y_corrected_bytes.append(int(y_corrected[i]*100).to_bytes(4,"big",signed=True))
            #z_corrected_bytes.append(int(z_corrected[i]*100).to_bytes(4,"big",signed=True))
        #Create a pandas data frame with the 3 axis
        #CalibratedData = pd.DataFrame({"AvgX": x_corrected_bytes, "AvgY": y_corrected_bytes, "AvgZ": z_corrected_bytes})
        #Write this data to CSV in data_storage folder
        #CalibratedData.to_csv(file_path + self.filename + "_avgdata_calibrated.csv")

    #Function specifically for Adam and UBSS
    def AdamCollectData(self):
        #Open Serial Port
        ser = self.OpenSerialPort()
        #Config Quadmag
        self.Config_QuadMag(ser)
        #Get filepath
        file_path = 'data_storage/'
        file_csv = file_path + self.filename + '_collectdata.csv'
        #Open CSV file
        with open(file_csv,mode="w") as csv_file:
            csvwriter = csv.writer(csv_file)
            #This is initializing command for serial port -> b'\x06' = continuous measurement mode
            command = b'\x06'
            command = command + b'\x00\x00' #artifact of removing user defined sample rate/on-board averaging
            mags_enabled = 0b1111 #All mags are enabled
            command = command + (mags_enabled).to_bytes(1, byteorder='big') #Add Mags into command
            command = command + (int(self.CollectionTime)).to_bytes(6, byteorder='big') #Add collection time into command
            #Adding file headers and writing to csv
            csvwriter.writerow(["Packet Flag","System Time (sec)","B1-X","B1-Y","B1-Z","B2-X","B2-Y","B2-Z","B3-X","B3-Y","B3-Z","B4-X","B4-Y","B4-Z"])
            #print('Command: ',command)
            #Write command to serial
            ser.write(command)
            #Taking measurements and verifying that data is collected properly
            total_measurements = 0
            expected_measurements = (int(self.CollectionTime)) * int(self.SampleRate)
            invalid_packet_count = 0
            invalid_packet_threshold = int(float(expected_measurements) * 0.1)  #10% of expected measurements
            print_threshold = int(float(expected_measurements) * 0.05) #5% of expected measurements
            return_string = ""
            while 1:
                #Get data from QM
                returned_bytes_string = dcl.get_response_helper(ser)
                #print('returned bytes: ',returned_bytes_string)
                # Stops the python program from attempting invalid string
                # operations....
                if (returned_bytes_string == '') or (returned_bytes_string[1] == "COMPLETE"):
                    #return_string = "\nContinuous measurement completed successfully!"
                    #break
                    pass
                elif returned_bytes_string[1] == '':
                    return_string = "\nContinuous measurement completed successfully!"
                    break
                elif invalid_packet_count > invalid_packet_threshold:
                    return "\nToo many invalid packets received, continuous measurement did not complete successfully!"
                elif len(returned_bytes_string[1]) > 0:
                    total_measurements = total_measurements + 1
                    raw_data = returned_bytes_string[1].split(",")
                    processed_data = []
                    for val in range(len(raw_data)):
                        if (val == 0) or (val == 1):
                            processed_data.append(raw_data[val])
                        elif raw_data[val] == '':
                            pass
                        else:
                            processed = int(raw_data[val])/(0.3671*self.CycleCount + 1.5)/self.OverSamples
                            processed_data.append(str(float(processed)))
                    csvwriter.writerow(processed_data)
                    #write_file_raw.write(str(processed_data) + "\n")
                else:
                    invalid_packet_count = invalid_packet_count + 1

            print("\n******Finished a continuous measurement******\n")
            print("\nExpected Measurements: " + str(expected_measurements))
            print("\nMissing Measurements: " + str(expected_measurements - total_measurements) + "\n")
            print("\nInvalid Packets Received: " + str(invalid_packet_count) + "\n")

        #Close Port
        ser.close()
        return return_string

    #This function is to open the serial port and try to connect to the Quad-Mag
    def OpenSerialPort(self): 
        baudrate = 115200  # Pre-Defined
        timeout = 3  # Pre-Defined
        tries = 5  # Arbitrary number of times we try to open serial port before giving up
        port = '/dev/ttyAMA0'
        while tries > 0:  # Attempt to establish serial port connection
            try:
                ser = serial.Serial(
                    port, baudrate, timeout=timeout, write_timeout=timeout)
                print("Serial port", port, "was opened successfully\n")
                break
            except serial.SerialException:
                print("Could not open", port,
                    "check connection or port configuration")
                tries -= 1
        if tries == 0:
            print("Failed to open specified port! Exiting...")
            sys.exit()
        return ser
    
    #This function is to config the QuadMag. All data collection functions call this
    def Config_QuadMag(self, ser):
        #ser = self.OpenSerialPort()
        #Set first hex to QM config
        command = b'\x01'
        #Setting Cycle count
        if self.CycleCount == 100:
            command = command + b'\x00\x64'
        elif self.CycleCount == 200:
            command = command + b'\x00\xC8'
        elif self.CycleCount == 400:
            command = command + b'\x01\x90'
        elif self.CycleCount == 800:
            command = command + b'\x03\x20'
        #Set Sample Rate    
        if self.SampleRate == 75:
            command = command + b'\x03'
        elif self.SampleRate == 1.2:
            command = command + b'\x09'
        else:
            #Setting to default of 37 Hz
            command = command + b'\x04'
        #Setting oversamples
        command = command + int(self.OverSamples).to_bytes(1, byteorder='big')
        #Final command
        command = command + int(0).to_bytes(5, byteorder='big')
        #Write command to serial
        ser.write(command)
        print(f"command={command}")
        UpdateConfigs = dcl.get_response_helper(ser)
        #print(UpdateConfigs)
        #ser.close()

        return UpdateConfigs

    #Getter and Setter functions below

    def getSampleRate(self) -> float:
        return self.SampleRate
    def setSampleRate(self, SampleRate: float) -> None:
        self.SampleRate = SampleRate

    def getCollectionTime(self) -> float:
        return self.CollectionTime
    def setCollectionTime(self, CollectionTime: float) -> None:
        self.CollectionTime = CollectionTime

    def getMode(self) -> float:
        return self.Mode
    def setMode(self, Mode: float) -> None:
        self.Mode = Mode
    def getDataLength(self) -> int:
        return self.DataLength
    def setDataLength(self, DataLength: int) -> None:
        self.DataLength = DataLength

    def getCycleCount(self) -> int:
        return self.CycleCount
    def setCycleCount(self, CycleCount: int) -> None:
        self.CycleCount = CycleCount

    def getOverSamples(self) -> int:
        return self.OverSamples
    def setOverSamples(self, OverSamples: int) -> None:
        self.OverSamples = OverSamples
        
    def getIGRF(self) -> int:
        return self.IGRF
    def setIGRF(self, IGRF: int) -> None:
        self.IGRF = IGRF

    def getfilename(self) -> str:
        return self.filename
    def setfilename(self, filename: str) -> None:
        self.filename = filename

    def getMagReadings(self) -> list:
        return self.mag_readings
