from sys import byteorder
import numpy as np
import matplotlib.pyplot as plt
#import keyboard
import time

from . import data_plotting_lib as dpl
from . import data_decoding_lib as ddl

###Various Command Flags###
#
# s -> standard config values
# d -> debug mode (helpful messages are printed to console)
# v -> verbose mode (all serial input is output to console)
# 1 -> linearity test
# 2 -> stability test
# 3 -> sensitivity Test
# 4 -> linear frequency response test
#

###Command Functions###

def set_mag_config(ser, flag):
    # Function Definition: Sets the config of the magnetometer
    # Input: Serial Object, Flag that contains options for function eg. verbose (v), debug (d), standard (s)
    # Output: String that holds the current mag config values
    allDefault = 'Y'
    if flag.find('s') == -1:
        allDefault = input(
            "\nDo you want to use all default values for the magnetometer config (Y/n)?\n")
    command = ""
    if allDefault != 'Y':
        command = b'\x01'
        cycleCount = input(
            "What cycle count do you want the magnetometers to run at (Leave blank for default value)?\nEnter here: ")
        if cycleCount == "":
            command = command + b'\x03\x20'
        else:
            command = command + int(cycleCount).to_bytes(2, byteorder='big')
        tmrc_switcher = {
            '0': 0x00,  # 600 Hz
            '1': 0x01,  # 300 Hz
            '2': 0x02,  # 150 Hz
            '3': 0x03,  # 75 Hz
            '4': 0x04,  # 37 Hz
            '5': 0x05,  # 18 Hz
            '6': 0x06,  # 9 Hz
            '7': 0x07,  # 4.5 Hz
            '8': 0x08,  # 2.3 Hz
            '9': 0x09,  # 1.2 Hz
            '10': 0x0A,  # 0.6 Hz
            '11': 0x0B,  # 0.3 Hz
            '12': 0x0C,  # 0.15 Hz
            '13': 0x0D  # 0.075 Hz
        }
        tmrcIndex = input("What frequency do you want the magnetometers to sample at (Leave blank for default value)? \n0: 600 Hz\n1: 300 Hz\n2: 150 Hz\n3: 75 Hz\n4: 37 Hz\n5: 18 Hz\n6: 9 Hz\n7: 4.5 Hz\n8: 2.3 Hz\n9: 1.2 Hz\n10: 0.6 Hz\n11: 0.3 Hz\n12: 0.15 Hz\n13: 0.075 Hz\nEnter Here: ")
        if (int(tmrcIndex) < 0 or int(tmrcIndex) > 13) and tmrcIndex != "":
            print("Invalid tmrc index...try again")
            set_mag_config(ser, flag)
        if tmrcIndex == "":
            command = command + b'\x04'
        else:
            tmrcVal = tmrc_switcher.get(
                tmrcIndex, lambda ser: "Failed to retrieve tmrc value!")
            command = command + \
                int(tmrcVal).to_bytes(1, byteorder='big')

        over_samples = input("How many oversamples do you want (1-256)?\n Enter Here: ")
        if (int(over_samples) < 0 or int(over_samples) > 256) and over_samples != "":
            print("Invalid number of oversamples...try again")
            set_mag_config(ser, flag)
        if over_samples == "":
            command = command + b'\x01' + int(0).to_bytes(5, byteorder='big')
        else:
            over_samples = over_samples if int(over_samples) != 0 else over_samples == '256'
            command = command + \
                int(over_samples).to_bytes(1, byteorder='big') + \
                int(0).to_bytes(5, byteorder='big')
    else:
        #command = b'\x01\x00\x64\x00\x01\x00\x00\x00\x00\x00'  # - 100 cycle counts. 1 oversamples
        #command = b'\x01\x00\xC8\x00\x04\x00\x00\x00\x00\x00' # - 200 cycle counts, 4 oversamples
        #command = b'\x01\x01\x90\x00\x01\x00\x00\x00\x00\x00' # - 400 cycle counts, 1 oversamples
        command = b'\x01\x03\x20\x00\x01\x00\x00\x00\x00\x00' # - 800 cycle counts, 1 oversamples
    ser.write(command)
    if flag.find('d') != -1:
        print("DEBUG: This is the command you just sent: " + str(command))
    updatedConfig = get_response_helper(ser)
    print('updatedConfig: ', updatedConfig)
    get_response_helper(ser) #Throwaway completion message
    if updatedConfig[0:8] != command[1:5].hex():
        print("Failed to correctly update config of magnetometers!")
        print("New config: " + updatedConfig[0:8])
        print("What the config should be: " + command[1:5].hex())
    else:
        return (updatedConfig)


def set_imu_config(ser, flag):
    # Function Definition: Sets the config of the the imu
    # Input: Serial Object, Flag that contains options for function eg. verbose (v), debug (d), standard (s)
    # Output: String that holds the current imu config values
    allDefault = 'Y'
    if flag.find('s') == -1:
        allDefault = input(
            "\nDo you want to use all default values for the imu config (Y/n)?\n")
    command = ""
    if allDefault != 'Y':
        command = b'\x02'
        accOdr_switcher = {
            '0': 0x01,  # 0.78125 Hz
            '1': 0x02,  # 1.5625 Hz
            '2': 0x03,  # 3.125 Hz
            '3': 0x04,  # 6.25 Hz
            '4': 0x05,  # 12.5 Hz
            '5': 0x06,  # 25 Hz
            '6': 0x07,  # 50 Hz
            '7': 0x08,  # 100 Hz
            '8': 0x09,  # 200 Hz
            '9': 0x0a,  # 400 Hz
            '10': 0x0b,  # 800 Hz
            '11': 0x0c,  # 1600 Hz
        }
        accOdrIndex = input("\nWhat frequency do you want the accelerometer to sample at (Leave blank for default value)? \n0: 0.78125 Hz\n1: 1.5625 Hz\n2: 3.125 Hz\n3: 6.25 Hz\n4: 12.5 Hz\n5: 25 Hz\n6: 50 Hz\n7: 100 Hz\n8: 200 Hz\n9: 400 Hz\n10: 800 Hz\n11: 1600 Hz\nEnter Here: ")
        if accOdrIndex == "":
            command = command + b'\x0c'
        elif (int(accOdrIndex) < 0 or int(accOdrIndex) > 11) and accOdrIndex != "":
            print("Invalid acceleromter Odr index...try again")
            set_imu_config(ser, flag)
        else:
            accOdrVal = accOdr_switcher.get(
                accOdrIndex, lambda ser: "Failed to retrieve accelerometer Odr value!")
            command = command + int(accOdrVal).to_bytes(1, byteorder='big')
        accBwp_switcher = {
            '0': 0x00,  # osr4_avg1
            '1': 0x01,  # osr2_avg2
            '2': 0x02,  # norm_avg4
            '3': 0x03,  # cic_avg8
            '4': 0x04,  # res_avg18
            '5': 0x05,  # res_avg32
            '6': 0x06,  # res_avg64
            '7': 0x07  # res_avg128
        }
        accBwpIndex = input("What bandwidth parameter do you want for the accelerometer (Leave blank for default value)? \n0: osr4_avg1\n1: osr2_avg2\n2: norm_avg4\n3: cic_avg8\n4: res_avg18\n5: res_avg32\n6: res_avg64\n7: res_avg128\nEnter Here: ")
        if accBwpIndex == "":
            command = command + b'\x02'
        elif (int(accBwpIndex) < 0 or int(accBwpIndex) > 7) and accBwpIndex != "":
            print("Invalid acceleromter Bwp index...try again")
            set_imu_config(ser, flag)
        else:
            accBwpVal = accBwp_switcher.get(
                accBwpIndex, lambda ser: "Failed to retrieve accelerometer Bwp value!")
            command = command + int(accBwpVal).to_bytes(1, byteorder='big')
        accFiltPerf_switcher = {
            '0': 0x00,  # ulp
            '1': 0x01,  # hp
        }
        accFiltPerfIndex = input(
            "What filter performance mode do you want for the accelerometer (Leave blank for default value)? \n0: ulp\n1: hp\nEnter Here: ")
        if accFiltPerfIndex == "":
            command = command + b'\x01'
        elif (int(accFiltPerfIndex) < 0 or int(accFiltPerfIndex) > 1) and accFiltPerfIndex != "":
            print("Invalid acceleromter Filter Perf index...try again")
            set_imu_config(ser, flag)
        else:
            accFiltPerfVal = accFiltPerf_switcher.get(
                accFiltPerfIndex, lambda ser: "Failed to retrieve accelerometer Filter Perf value!")
            command = command + \
                int(accFiltPerfVal).to_bytes(1, byteorder='big')
        accRange_switcher = {
            '0': 0x00,  # +/-2g
            '1': 0x01,  # +/-4g
            '2': 0x02,  # +/-8g
            '3': 0x03  # +/-16g
        }
        accRangeIndex = input(
            "What range do you want for the accelerometer (Leave blank for default value)? \n0: +/-2g\n1: +/-4g\n2: +/-8g\n3: +/-16g\nEnter Here: ")
        if accRangeIndex == "":
            command = command + b'\x01'
        elif (int(accRangeIndex) < 0 or int(accRangeIndex) > 1) and accRangeIndex != "":
            print("Invalid acceleromter range index...try again")
            set_imu_config(ser, flag)
        else:
            accRangeVal = accRange_switcher.get(
                accRangeIndex, lambda ser: "Failed to retrieve accelerometer range value!")
            command = command + int(accRangeVal).to_bytes(1, byteorder='big')
        gyrOdr_switcher = {
            '0': 0x06,  # 25 Hz
            '1': 0x07,  # 50 Hz
            '2': 0x08,  # 100 Hz
            '3': 0x09,  # 200 Hz
            '4': 0x0A,  # 400 Hz
            '5': 0x0B,  # 800 Hz
            '6': 0x0C,  # 1600 Hz
            '7': 0x0D,  # 3200 Hz
        }
        gyrOdrIndex = input(
            "What frequency do you want the gyroscope to sample at (Leave blank for default value)? \n0: 25 Hz\n1: 50 Hz\n2: 100 Hz\n3: 200 Hz\n4: 400 Hz\n5: 800 Hz\n6: 1600 Hz\n7: 3200 Hz\nEnter Here: ")
        if gyrOdrIndex == "":
            command = command + b'\x0c'
        elif (int(gyrOdrIndex) < 0 or int(gyrOdrIndex) > 7) and gyrOdrIndex != "":
            print("Invalid gyroscope Odr index...try again")
            set_imu_config(ser, flag)
        else:
            gyrOdrVal = gyrOdr_switcher.get(
                gyrOdrIndex, lambda ser: "Failed to retrieve gyroscope Odr value!")
            command = command + int(gyrOdrVal).to_bytes(1, byteorder='big')
        gyrBwp_switcher = {
            '0': 0x00,  # osr4
            '1': 0x01,  # osr2
            '2': 0x02,  # norm
        }
        gyrBwpIndex = input(
            "What bandwidth parameter do you want for the gyroscope (Leave blank for default value)? \n0: osr4\n1: osr22\n2: norm\nEnter Here: ")
        if gyrBwpIndex == "":
            command = command + b'\x02'
        elif (int(gyrBwpIndex) < 0 or int(gyrBwpIndex) > 2) and gyrBwpIndex != "":
            print("Invalid gyroscope Bwp index...try again")
            set_imu_config(ser, flag)
        else:
            gyrBwpVal = gyrBwp_switcher.get(
                gyrBwpIndex, lambda ser: "Failed to retrieve gyroscope Bwp value!")
            command = command + int(gyrBwpVal).to_bytes(1, byteorder='big')
        gyrNoisePerf_switcher = {
            '0': 0x00,  # ulp
            '1': 0x01,  # hp
        }
        gyrNoisePerfIndex = input(
            "What noise performance mode do you want for the gyroscope (Leave blank for default value)? \n0: ulp\n1: hp\nEnter Here: ")
        if gyrNoisePerfIndex == "":
            command = command + b'\x01'
        elif (int(gyrNoisePerfIndex) < 0 or int(gyrNoisePerfIndex) > 1) and gyrNoisePerfIndex != "":
            print("Invalid gyroscope Noise Perf index...try again")
            set_imu_config(ser, flag)
        else:
            gyrNoisePerfVal = gyrNoisePerf_switcher.get(
                gyrNoisePerfIndex, lambda ser: "Failed to retrieve gyroscope Noise Perf value!")
            command = command + \
                int(gyrNoisePerfVal).to_bytes(1, byteorder='big')
        gyrFiltPerf_switcher = {
            '0': 0x00,  # ulp
            '1': 0x01,  # hp
        }
        gyrFiltPerfIndex = input(
            "What filter performance mode do you want for the gyroscope (Leave blank for default value)? \n0: ulp\n1: hp\nEnter Here: ")
        if gyrFiltPerfIndex == "":
            command = command + b'\x01'
        elif (int(gyrFiltPerfIndex) < 0 or int(gyrFiltPerfIndex) > 1) and gyrFiltPerfIndex != "":
            print("Invalid gyroscope Filt Perf index...try again")
            set_imu_config(ser, flag)
        else:
            gyrFiltPerfVal = gyrFiltPerf_switcher.get(
                gyrFiltPerfIndex, lambda ser: "Failed to retrieve gyroscope Filt Perf value!")
            command = command + \
                int(gyrFiltPerfVal).to_bytes(1, byteorder='big')
        gyrRange_switcher = {
            '0': 0x00,  # +/-2000dps
            '1': 0x01,  # +/-1000dps
            '2': 0x02,  # +/-500dps
            '3': 0x03,  # +/-250dps
            '4': 0x04  # +/-125dps
        }
        gyrRangeIndex = input(
            "What range do you want for the gyroscope (Leave blank for default value)? \n0: +/-2000dps\n1: +/-1000dps\n2: +/-500dps\n3: +/-250dps\n4: +/-125dps\nEnter Here: ")
        if gyrRangeIndex == "":
            command = command + b'\x00'
        elif (int(gyrRangeIndex) < 0 or int(gyrRangeIndex) > 1) and gyrRangeIndex != "":
            print("Invalid gyroscope range index...try again")
            set_imu_config(ser, flag)
        else:
            gyrRangeVal = gyrRange_switcher.get(
                gyrRangeIndex, lambda ser: "Failed to retrieve gyroscope range value!")
            command = command + int(gyrRangeVal).to_bytes(1, byteorder='big')
    else:
        command = b'\x02\x0c\x02\x01\x01\x0c\x02\x01\x01\x00'
    ser.write(command)
    if flag.find('d') != -1:
        print("DEBUG: This is the command you just sent: " + str(command))
    updatedConfig = get_response_helper(ser)
    get_response_helper(ser) #Throwaway completion message
    if updatedConfig != command[1:10].hex():
        print("Failed to correctly update imu config!")
        print("New config: " + updatedConfig)
        print("What the config should be: " + command[1:10].hex())
    else:
        return (updatedConfig)


def get_mag_config(ser, flag):
    # Function Definition: Gets the config of the magnetometer
    # Input: Serial Object, Flag that contains options for function eg. verbose (v), debug (d)
    # Output: String that holds the current mag config values
    command = b'\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    ser.write(command)
    config = get_response_helper(ser)
    get_response_helper(ser) #Throwaway completion message
    if flag.find('d') != -1:
        print(config)
    return config


def get_imu_config(ser, flag):
    # Function Definition: Gets the config of the imu
    # Input: Serial Object, Flag that contains options for function eg. verbose (v), debug (d)
    # Output: String that holds the current imu config values
    command = b'\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    ser.write(command)
    config = get_response_helper(ser)
    get_response_helper(ser) #Throwaway completion message
    if flag.find('d') != -1:
        print(config)
    return config


def single_measurement(ser, flag):
    # Function Definition: Requests a single measurement from the quad-mag
    # Input: Serial Object, Flag that contains options for function eg. verbose (v), debug (d)
    # Output: String that tells the caller the measurement has been completed

    enabled_imu = True if flag.find('i') != -1 else False
    enabled_temperature = True if flag.find('t') != -1 else False
    enabled_verbose = True if flag.find('v') != -1 else False
    enabled_debug = True if flag.find('d') != -1 else False
    enabled_plotting = True if flag.find('p') != -1 else False


    write_file_name = ''
    file_path = 'data_storage/'
    while 1:
        write_file_name = input("\nWhat is the name of the file you want to write data to (don't include file extension, must be in a csv format)?\n")
        try:
            write_file_raw = open((file_path + write_file_name + '_raw_data.txt'), 'w+')
            write_file_processed = open((file_path + write_file_name + '_processed_data.txt'), 'w+')
            break
        except FileExistsError:
            print("\nThat file could not be written to...try again\n")
    sensor_configs = set_mag_config(ser, flag)
    sensor_configs_csv = sensor_configs[0:4] + "," + sensor_configs[6:8]
    if enabled_imu :
        sensor_configs = sensor_configs + set_imu_config(ser, flag)
        sensor_configs_csv = sensor_configs_csv + "," + sensor_configs[12:14] + ","
        sensor_configs_csv = sensor_configs_csv + "," + sensor_configs[22:24]
    command = b'\x05'
    disable_mags = input("\nDo you want to disable any mags (Y/n)? ") #all mags are enabled by default
    mags_enabled = 0b1111
    if disable_mags == 'Y' :
        mags_to_disable = input("\nEnter the mag numbers you would like to disable as a single string eg. 1234\n")
        if mags_to_disable.find('1') != -1 :
            mags_enabled = mags_enabled & 0b1110
        if mags_to_disable.find('2') != -1 :
            mags_enabled = mags_enabled & 0b1101
        if mags_to_disable.find('3') != -1 :
            mags_enabled = mags_enabled & 0b1011
        if mags_to_disable.find('4') != -1 :
            mags_enabled = mags_enabled & 0b0111
            
    command = command + (mags_enabled).to_bytes(1, byteorder='big') + (0).to_bytes(8,byteorder='big')

    for me in range(0,3) :
        if not((mags_enabled >> me) and 0b1) != int(sensor_configs[8+(me*2):10+(me*2)]) :
                print("\n***Failed to correctly update config of magnetometer" + str(me+1) + '***\n')

    command = command + (mags_enabled).to_bytes(1, byteorder='big')

    if enabled_imu :
        write_file_raw.write(
            "Mag Cycle Count, Mag Number of Oversamples, Accel Gain, Gyro Gain (readings are raw)\n")
        write_file_processed.write(
            "Mag Cycle Count, Mag Number of Oversamples, Accel Gain, Gyro Gain (readings are in lsb form)\n")
    else:
        write_file_raw.write(
            "Mag Cycle Count, Mag Number of Oversamples (readings are raw)\n")
        write_file_processed.write("Mag Cycle Count, Mag Number of Oversamples (readings are in lsb form)\n")

    write_file_raw.write(sensor_configs_csv + '\n\n')
    write_file_processed.write(str(int(sensor_configs_csv[0:4], 16)) + ',' + str(int(sensor_configs_csv[5:7], 16)) + '\n\n')

    if enabled_temperature  and enabled_imu :
        write_file_processed.write(
            "System Time (sec), B1-X , B1-Y, B1-Z, B2-X, B2-Y, B2-Z, B3-X, B3-Y, B3-Z, B4-X, B4-Y, B4-Z, Acc-X, Acc-Y, Acc-Z, Gyr-X, Gyr-Y, Gyr-Z, Temp\n")
    elif not enabled_temperature and not enabled_imu :
        write_file_processed.write(
            "System Time (sec), B1-X , B1-Y, B1-Z, B2-X, B2-Y, B2-Z, B3-X, B3-Y, B3-Z, B4-X, B4-Y, B4-Z\n")
    elif enabled_imu :
        write_file_processed.write(
            "System Time (sec), B1-X , B1-Y, B1-Z, B2-X, B2-Y, B2-Z, B3-X, B3-Y, B3-Z, B4-X, B4-Y, B4-Z, Acc-X, Acc-Y, Acc-Z, Gyr-X, Gyr-Y, Gyr-Z\n")
    else:
        write_file_processed.write(
            "System Time (sec), B1-X , B1-Y, B1-Z, B2-X, B2-Y, B2-Z, B3-X, B3-Y, B3-Z, B4-X, B4-Y, B4-Z, Temp\n")

    ser.write(command)

    if enabled_debug:
        print("\nDEBUG: THIS IS THE COMMAND YOU JUST SENT\n" + str(command) + "\n")

    total_measurements = 0
    invalid_packet_count = 0
    invalid_packet_threshold = 10  #10% of expected measurements
    return_string = ""
    while 1:
        
        returned_bytes_string = get_response_helper(ser)
        # Stops the python program from attempting invalid string
        # operations....
        if returned_bytes_string[1] == "COMPLETE":
            return_string = "\nContinuous measurement completed successfully!"
            break
        elif invalid_packet_count > invalid_packet_threshold:
            return "\nToo many invalid packets received, continuous measurement did not complete successfully!"
        elif len(returned_bytes_string[1]) > 0:
            total_measurements = total_measurements + 1
            if enabled_verbose:
                print(str(total_measurements) + "," + returned_bytes_string[1])
            write_file_raw.write(returned_bytes_string[0] + "\n")
            write_file_processed.write(returned_bytes_string[1] + "\n")
        else:
            invalid_packet_count = invalid_packet_count + 1

    print("\n******Finished a single measurement******\n")
    print("\nInvalid Packets Received: " + str(invalid_packet_count) + "\n")

    write_file_raw.close()
    
    if enabled_plotting:
        create_plots = input(
            "Data has finished collecting...do you want to create plots (Y/n)\n")
        if create_plots == 'Y':
            dpl.plot_data('u', filename=write_file_name)
    
    write_file_processed.close()

    return return_string


def continuous_measurement(ser, flag):
    # Function Definition: Requests continuous measurements from mag for specified period of time
    # Input: Serial Object, Flag that contains options for function eg. verbose (v), debug (d)
    # Output: String that tells the caller the measurements have been completed

    enabled_imu = True if flag.find('i') != -1 else False
    enabled_temperature = True if flag.find('t') != -1 else False
    enabled_verbose = True if flag.find('v') != -1 else False
    enabled_debug = True if flag.find('d') != -1 else False
    enabled_plotting = True if flag.find('p') != -1 else False

    print('begin contin measure: ',flag)
    write_file_name = ''
    file_path = 'data_storage/'
    while 1:
        write_file_name = input("\nWhat is the name of the file you want to write data to (don't include file extension, must be in a csv format)?\n")
        try:
            write_file_raw = open((file_path + write_file_name + '_raw_data.txt'), 'w+')
            write_file_processed = open((file_path + write_file_name + '_processed_data.txt'), 'w+')
            break
        except FileExistsError:
            print("\nThat file could not be written to...try again\n")
    sensor_configs = set_mag_config(ser, flag)
    print("aft sensor_configs",flag)
    sensor_configs_csv = sensor_configs[0:4] + "," + sensor_configs[6:8]
    if enabled_imu :
        sensor_configs = sensor_configs + set_imu_config(ser, flag)
        sensor_configs_csv = sensor_configs_csv + "," + sensor_configs[12:14]
        sensor_configs_csv = sensor_configs_csv + "," + sensor_configs[22:24]
    command = b'\x06'
    measurement_length = 0.00
    sample_rate = 457.7786*np.power(0.9966, int(sensor_configs[0:4], 16)) #attempted exponential fit to sample rate i.e. not super accurate
    command = command + b'\x00\x00' #artifact of removing user defined sample rate/on-board averaging

    disable_mags = input("\nDo you want to disable any mags (Y/n)? ") #all mags are enabled by default
    mags_enabled = 0b1111
    if disable_mags == 'Y' :
        mags_to_disable = input("\nEnter the mag numbers you would like to disable as a single string eg. 1234\n")
        if mags_to_disable.find('1') != -1 :
            mags_enabled = mags_enabled & 0b1110
        if mags_to_disable.find('2') != -1 :
            mags_enabled = mags_enabled & 0b1101
        if mags_to_disable.find('3') != -1 :
            mags_enabled = mags_enabled & 0b1011
        if mags_to_disable.find('4') != -1 :
            mags_enabled = mags_enabled & 0b0111

    command = command + (mags_enabled).to_bytes(1, byteorder='big')

    for me in range(0,3) :
        if not((mags_enabled >> me) and 0b1) != int(sensor_configs[8+(me*2):10+(me*2)]) :
                print("\n***Failed to correctly update config of magnetometer" + str(me+1) + '***\n')

    measurement_length = input(
        "\nEnter how long to take measurements for in seconds (leave blank or enter 0 for custom period): ")
    if measurement_length == '' or measurement_length == '0' :
        measurement_length = 4294967295
        command = command + (measurement_length).to_bytes(6, byteorder='big') #keyboard interrupt will cut off measurement
    else :
        command = command + (int(measurement_length)).to_bytes(6, byteorder='big')
    
    if enabled_imu :
        write_file_raw.write(
            "Mag Cycle Count, Mag Number of Oversamples, Accel Gain, Gyro Gain (readings are raw)\n")
        write_file_processed.write(
            "Mag Cycle Count, Mag Number of Oversamples, Accel Gain, Gyro Gain (readings are in lsb form)\n")
    else:
        write_file_raw.write(
            "Mag Cycle Count, Mag Number of Oversamples (readings are raw)\n")
        write_file_processed.write("Mag Cycle Count, Mag Number of Oversamples (readings are in lsb form)\n")

    write_file_raw.write(sensor_configs_csv + '\n\n')
    write_file_processed.write(str(int(sensor_configs_csv[0:4], 16)) + ',' + str(int(sensor_configs_csv[5:7], 16)) + '\n\n')

    if enabled_temperature  and enabled_imu :
        write_file_processed.write(
            "Packet Flag, System Time (sec), B1-X , B1-Y, B1-Z, B2-X, B2-Y, B2-Z, B3-X, B3-Y, B3-Z, B4-X, B4-Y, B4-Z, Acc-X, Acc-Y, Acc-Z, Gyr-X, Gyr-Y, Gyr-Z, Temp\n")
    elif not enabled_temperature and not enabled_imu :
        write_file_processed.write(
            "Packet Flag, System Time (sec), B1-X , B1-Y, B1-Z, B2-X, B2-Y, B2-Z, B3-X, B3-Y, B3-Z, B4-X, B4-Y, B4-Z\n")
    elif enabled_imu :
        write_file_processed.write(
            "Packet Flag, System Time (sec), B1-X , B1-Y, B1-Z, B2-X, B2-Y, B2-Z, B3-X, B3-Y, B3-Z, B4-X, B4-Y, B4-Z, Acc-X, Acc-Y, Acc-Z, Gyr-X, Gyr-Y, Gyr-Z\n")
    else:
        write_file_processed.write(
            "Packet Flag, System Time (sec), B1-X , B1-Y, B1-Z, B2-X, B2-Y, B2-Z, B3-X, B3-Y, B3-Z, B4-X, B4-Y, B4-Z, Temp\n")
    print(command)
    ser.write(command)
    if enabled_debug:
        print("\nDEBUG: THIS IS THE COMMAND YOU JUST SENT\n" + str(command) + "\n")

    total_measurements = 0
    expected_measurements = (int(measurement_length)) * int(sample_rate)
    invalid_packet_count = 0
    invalid_packet_threshold = int(float(expected_measurements) * 0.1)  #10% of expected measurements
    print_threshold = int(float(expected_measurements) * 0.05) #5% of expected measurements
    return_string = ""
    while 1:

        # Print roughly how many measurements have been taken periodically
        if enabled_verbose and total_measurements % print_threshold == 0:
            print(str(total_measurements) + "/" +
                  str(expected_measurements) + " measurements received")
        
        returned_bytes_string = get_response_helper(ser)
        # Stops the python program from attempting invalid string
        # operations....
        if returned_bytes_string[1] == "COMPLETE":
            return_string = "\nContinuous measurement completed successfully!"
            break
        elif invalid_packet_count > invalid_packet_threshold:
            return "\nToo many invalid packets received, continuous measurement did not complete successfully!"
        elif len(returned_bytes_string[1]) > 0:
            total_measurements = total_measurements + 1
            if enabled_verbose:
                print(str(total_measurements) + "," + returned_bytes_string[1])
            write_file_raw.write(returned_bytes_string[0] + "\n")
            write_file_processed.write(returned_bytes_string[1] + "\n")
        else:
            invalid_packet_count = invalid_packet_count + 1

        try:  # Used try so that if user pressed other than the given key error will not be shown or do nothing
            if keyboard.is_pressed('q'):  # if key 'q' is pressed 
                stop_all_operations(ser, flag)
                write_file_raw.close()
                write_file_processed.close()
                return '\nYou have manually forced this measurement session to end, continuous measurement completed successfully!'  # finishing the loop
        except :
            continue #aka do nothing

    print("\n******Finished a continuous measurement******\n")
    print("\nExpected Measurements: " + str(expected_measurements))
    print("\nMissing Measurements: " + str(expected_measurements - total_measurements) + "\n")
    print("\nInvalid Packets Received: " + str(invalid_packet_count) + "\n")

    write_file_raw.close()
    
    if enabled_plotting:
        create_plots = input(
            "Data has finished collecting...do you want to create plots (Y/n)\n")
        if create_plots == 'Y':
            dpl.plot_data('u', filename=(write_file_name + '_processed_data.txt'))
    
    write_file_processed.close()

    return return_string


def send_data(ser, flag):
    # Function Definition: Send any data we have available
    # Input: Serial object, Flag that contains options for function eg. verbose (v), debug (d)
    # Output: String that holds data if it was valid
    command = b'\x07\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    ser.write(command)
    returned_bytes_string = get_response_helper(ser)
    if returned_bytes_string[1] == "":
        return "The data was either corrupted or invalid"
    else:
        return returned_bytes_string[1]
    return "The data checksum was invalid"


def stop_all_operations(ser, flag):
    # Function Definition: Stops all sensors and puts controller in ulp mode
    # Input: serial object, Flag that contains options for function eg. verbose (v), debug (d)
    # Output: String confirming whether the command was successfully executed
    command = b'\x08\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    ser.write(command)
    returned_bytes_string = get_response_helper(ser)
    if returned_bytes_string[1] == "COMPLETE":
        return "\nSuccessfully stopped all operations and put controller into low power mode!\n"
    return "\nDid not successfully stop all operations, an error occurred!\n"

###Helper Functions###


def get_response_helper(ser):
    # Temporary to create object
    returned_bytes = (0).to_bytes(1, byteorder='big')
    returned_bytes = ser.read(1)  # Gets packet flag
    #print('reading 1st byte: ',returned_bytes)
    packet_flag = returned_bytes.hex()
    # print('Packet Flag: ',packet_flag)
    # Stops the python program from attempting invalid string
    # operations....
    
    if packet_flag == "0a":
        return ['', "COMPLETE"]
    elif packet_flag == '':
        return ['','']
    # Debug Flag
    elif packet_flag == '01':
        returned_bytes = ser.read(17)
        if len(returned_bytes) == 17:
            if ddl.valid_checksum(returned_bytes, packet_flag):
                dc = ddl.decode_serial_byte_stream_quad(returned_bytes, packet_flag)
                dc[0] = packet_flag + dc[0]
                dc[1] = packet_flag + "," + dc[1]
                return dc
            else:
                return ""
    # Mag Config Flag
    elif packet_flag == '02':
        return (ser.read(8).hex())
    # IMU Config Flag
    elif packet_flag == '03':
        return (ser.read(9).hex())
    # Mag Data Only Flag
    elif packet_flag == '04':
        returned_bytes = ser.read(44)
        if len(returned_bytes) == 44:
            if ddl.valid_checksum(returned_bytes, packet_flag):
                dc = ddl.decode_serial_byte_stream_quad(returned_bytes, packet_flag)
                dc[0] = packet_flag + dc[0]
                dc[1] = packet_flag + "," + dc[1]
                return dc
            else:
                return ""
    # All Sensors Data Flag
    elif packet_flag == '05':
        returned_bytes = ser.read(58)
        if len(returned_bytes) == 58:
            if ddl.valid_checksum(returned_bytes, packet_flag):
                dc = ddl.decode_serial_byte_stream_quad(returned_bytes, packet_flag)
                dc[0] = packet_flag + dc[0]
                dc[1] = packet_flag + "," + dc[1]
                return dc
            else:
                return ""
    # Mag and TMP data flag
    elif packet_flag == '06':
        returned_bytes = ser.read(46)
        if len(returned_bytes) == 46:
            if ddl.valid_checksum(returned_bytes, packet_flag):
                dc = ddl.decode_serial_byte_stream_quad(returned_bytes, packet_flag)
                dc[0] = packet_flag + dc[0]
                dc[1] = packet_flag + "," + dc[1]
                return dc
            else:
                return ""
    # Mag and IMU data flag
    elif packet_flag == '07':
        returned_bytes = ser.read(56)
        if len(returned_bytes) == 56:
            if ddl.valid_checksum(returned_bytes, packet_flag):
                dc = ddl.decode_serial_byte_stream_quad(returned_bytes, packet_flag)
                dc[1] = packet_flag + "," + dc[1]
                return dc
            else:
                return ""
    # Invalid Packet
    else:
        return ""


def get_command(ser, f):
    # Function Definition: Gets the command to be run during this loop iteration based on user input
    # Input: None
    # Output: Function pointer based on user input
    #print('get_command: ',f)
    command_switcher = {
        '1': set_mag_config,
        '2': set_imu_config,
        '3': get_mag_config,
        '4': get_imu_config,
        '5': single_measurement,
        '6': continuous_measurement,
        '7': send_data,
        '8': stop_all_operations
    }
    # Get command to be run from the user
    while 1:
        command_num = input(
            "What command would you like to send?\n\n1: Set Mag Config\n2: Set IMU Config\n3: Get Mag Config\n4: Get IMU Config\n5: Take Single Measurement\n6: Take Continuous Measurement\n7: Send Available Data\n8: Stop All Operations\n\nEnter a command number here (1-8): ")
        command = command_switcher.get(
            command_num, lambda ser: "Command failed!")
        if int(command_num) < 1 or int(command_num) > 8:
            print("\nInvalid command number", command_num, "try again\n")
        else:
            break
    f = f + 'vpdu'
    #print('End get_command: ', f)
    return command(ser, f)
