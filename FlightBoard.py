import os
import time
import smbus2
from MCP4725 import MCP4725
#from adafruit_mcp4725 import MCP4725  # Assuming MCP4725 is in the same directory
from busio import I2C
from ADS1x15 import ADS1x15
from ADS1x15 import ADS1015
import csv
from datetime import datetime
import logging

#Make instances for DAC and ADC
dac = MCP4725(address=0x60)
nons = ADS1015(address=0x4a)
shunted = ADS1015(address=0x48)
refer = ADS1015(address=0x49)

def adc_read1():
    start = time.time()
    A0read = nons.read_adc(0, 1, 3300)
    A1read = nons.read_adc(1, 1, 3300)
    A2read = nons.read_adc(2, 1, 3300)
    end = time.time()
    print(f"{A0read}")
    print(f"{A1read}")
    print(f"{A2read}")
    print(f"{end-start}")
    
def adc_read2():
    start = time.time()
    A0read = shunted.read_adc(0, 1, 3300)
    A1read = shunted.read_adc(1, 1, 3300)
    A2read = shunted.read_adc(2, 1, 3300)
    end = time.time()
    print(f"{A0read}")
    print(f"{A1read}")
    print(f"{A2read}")
    print(f"{end-start}")

def adc_read3():
    start = time.time()
    A0read = refer.read_adc(0, 1, 3300)
    A1read = refer.read_adc(1, 1, 3300)
    A2read = refer.read_adc(2, 1, 3300)
    end = time.time()
    print(f"{A0read}")
    print(f"{A1read}")
    print(f"{A2read}")
    print(f"{end-start}")

def adc_reada():
    start = time.time()
    A0read = nons.read_adc(1, 1, 3300)
    A1read = shunted.read_adc(0, 1, 3300)
    A2read = refer.read_adc(2, 1, 3300)
    end = time.time()
    print(f"{A0read}")
    print(f"{A1read}")
    print(f"{A2read}")
    print(f"{end-start}")

def sweep_dac():
    duration=1.0
    steps = 4096
    delay = duration/steps

    t = time.time()
    for value in range(steps):
        dac.set_voltage(value)
    elapsed = time.time() - t
    print(f"{elapsed}")

def set_adc_rate():
    rate = input("128, 250, 490, 920, 1600, 2400, 3300: \n")
    adc._data_rate_config(int(rate))


def set_dac():
    voltage = input("Set to (bits): ")
    value = int(voltage)
    print(f"set to {voltage}")
    dac.set_voltage(value, persist=False)


""" SWEEPADC ARCHITECTURE -------------------------------"""

def adc_read_all_channels(adc):
    A0r = adc.read_adc(0, 1, 3300)
    A1r = adc.read_adc(1, 1, 3300)
    A2r = adc.read_adc(2, 1, 3300)
    return A0r, A1r, A2r

def tocsv(filename, data):
    with open(filename, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['step', 'A0read', 'A1read', 'A2read'])
        csvwriter.writerows(data)

def adc_sweep(adc, filename=None, steps=4096):
    data = []
    adc._data_rate_config(3300)
    start = time.time()
    
    for sweep in range(int(steps)):
        A0read, A1read, A2read = adc_read_all_channels(adc)
        data.append([sweep, A0read, A1read, A2read])
        
    end = time.time()
    elapsed = end-start

    #save to csv
    assert(filename != None)
    tocsv(filename,data)

    print(f"Completed {steps} steps in {elapsed} seconds.")
    return



""" SWEEP ARCHITECTURE ----------------------------------"""

def adc_read_all(adc):
    A0r = adc.read_adc(channel=0, gain=1, data_rate=3300)
    A1r = adc.read_adc(channel=1, gain=1, data_rate=3300)
    A2r = adc.read_adc(channel=2, gain=1, data_rate=3300)
    # A1r = 22
    # A0r = 44
    return A0r, A1r, A2r

def tocsv(filename, data):
    with open(filename, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['step', 'A0read', 'A1read', 'A2read'])
        csvwriter.writerows(data)

def adc_sweep(adc, filename=None, steps=4096):
    data = []
    adc._data_rate_config(3300)
    start = time.time()
    
    for sweep in range(int(steps)):
        A0read, A1read, A2read = adc_read_all(adc)
        data.append([sweep, A0read, A1read, A2read])
        
    end = time.time()
    elapsed = end-start

    #save to csv
    assert(filename != None), 'bruh Enter a filename.'
    tocsv(filename,data)

    print(f"{steps} steps in {elapsed}s.")
    return


"""ADC+DAC SWEEP ARCHITECTURE """

def adc_read_all(nons, shunted, refer):
    A0r = nons.read_adc(channel=0, gain=1, data_rate=3300)
    A1r = shunted.read_adc(channel=1, gain=1, data_rate=3300)
    A2r = refer.read_adc(channel=2, gain=1, data_rate=3300)
    # A1r = 22
    # A0r = 44
    return A0r, A1r, A2r


def adc_dac_sweep(nons, shunted, refer, filename=None, steps=4096):
    data = []
    nons._data_rate_config(3300)
    shunted._data_rate_config(3300)
    refer._data_rate_config(3300)
    start = time.time()
    
    for sweep in range(int(steps)):
        A0read, A1read, A2read = adc_read_all(nons=nons, shunted=shunted, refer=refer)
        data.append([sweep, A0read, A1read, A2read])

        dac.set_voltage(sweep)
        # time.sleep(.003)


    end = time.time()
    elapsed = end-start

    #save to csv
    assert(filename != None), 'bruh Enter a filename.'
    tocsv(filename,data)

    print(f"{steps} steps in {elapsed}s.")
    return

"""START/STOP ARCHITECTURE"""

def start_stop(filename=None):
    #initialize logging
    logging.basicConfig(level=logging.INFO)
    
    #start continuous conversion on channel 0 for all ADCs
    data = []
    # print(f"Starting continuous conversion for all ADCs")
    nons.start_adc(channel=1, gain=1, data_rate=3300)
    shunted.start_adc(channel=0, gain=1, data_rate=3300)
    refer.start_adc(channel=2, gain=1, data_rate=3300)
    
    try:
        #read conversion results for 5 seconds
        start = time.time()
        for value in range(4096):
            
            result1 = nons.get_last_result()
            result2 = shunted.get_last_result()
            result3 = refer.get_last_result()
            # print(f"nons Result: {result1}, shunted Result: {result2}, refer Result: {result3}")
            data.append([value, result1, result2, result3])
            dac.set_voltage(value)
            # time.sleep(0.01)
            
    finally:
        #stop continuous conversion for all ADCs
        print(f"Stopping continuous conversion for all ADCs")
        nons.stop_adc()
        shunted.stop_adc()
        refer.stop_adc()
        tocsv(filename,data)
        finished = time.time()
        elapsed = finished-start
        print(f"{elapsed}")

"""START/STOP WEENED ARCHITECTURE"""

def start_stop_weened(filename=None):
    #initialize logging
    logging.basicConfig(level=logging.INFO)
    
    #start continuous conversion on channel 0 for all ADCs
    data = []
    # print(f"Starting continuous conversion for all ADCs")
    nons.start_adc(channel=1, gain=1, data_rate=3300)
    shunted.start_adc(channel=0, gain=1, data_rate=3300)
    refer.start_adc(channel=2, gain=1, data_rate=3300)
    
    try:
        #read conversion results for 5 seconds
        start = time.time()
        value = 0
        while value < 4096:
            dac.set_voltage(value)
            result1 = nons.get_last_result()
            result2 = shunted.get_last_result()
            result3 = refer.get_last_result()
            # print(f"nons Result: {result1}, shunted Result: {result2}, refer Result: {result3}")
            data.append([value, result1, result2, result3])

            if value < 1000:
                value += 50
            elif value > 2700:
                value += 50
            else:
                value += 1  

            
    finally:
        #stop continuous conversion for all ADCs
        print(f"Stopping continuous conversion for all ADCs")
        nons.stop_adc()
        shunted.stop_adc()
        refer.stop_adc()
        tocsv(filename,data)
        finished = time.time()
        elapsed = finished-start
        print(f"{elapsed}")


"""START/STOP WEENED CONTINUOUS DATA TAKING ARCHITECTURE"""

# define folder path
folder_path = "/OPV/csv_files"

def start_stop_weened_cont(filename=None):
    #initialize logging
    logging.basicConfig(level=logging.INFO)
    
    #start continuous conversion on channel 0 for all ADCs
    data = []
    # print(f"Starting continuous conversion for all ADCs")
    nons.start_adc(channel=1, gain=1, data_rate=3300)
    shunted.start_adc(channel=0, gain=1, data_rate=3300)
    refer.start_adc(channel=2, gain=1, data_rate=3300)
    
    try:
        #read conversion results for 5 seconds
        start = time.time()
        value = 0
        while value < 4096:
            dac.set_voltage(value)
            result1 = nons.get_last_result()
            result2 = shunted.get_last_result()
            result3 = refer.get_last_result()
            # print(f"nons Result: {result1}, shunted Result: {result2}, refer Result: {result3}")
            data.append([value, result1, result2, result3])

            if value < 1000:
                value += 50
            elif value > 2700:
                value += 50
            else:
                value += 1  

            
    finally:
        #stop continuous conversion for all ADCs
        print(f"Stopping continuous conversion for all ADCs")
        nons.stop_adc()
        shunted.stop_adc()
        refer.stop_adc()
        
        # create a directory if it doesn't exist
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        
        fullpath = os.path.join(folder_path, filename)
        tocsv(fullpath, data)
        
        finished = time.time()
        elapsed = finished-start
        print(f"{elapsed}")



""" MAIN ----------------------------------"""

def main():
    counter = 1
    
    while True:
        uinput = input("'read s#' 'read sa' 'setdac' 'startstop' 'startstop w' 'startstop wc' 'sweepdac' 'adcrate' 'sweepadc' 'sweepadcdac' 'exit'\n")
        if uinput.lower() == 'read s1':
            adc_read1()
        elif uinput.lower() == 'read s2':
            adc_read2()
        elif uinput.lower() == 'read s3':
            adc_read3()
        elif uinput.lower() == 'startstop':
            fname = input("filename to write to (with .csv)\n")
            start_stop(filename=fname)
        elif uinput.lower() == 'startstop w':
            fname = input("filename to write to (with .csv)\n")
            start_stop_weened(filename=fname)
        elif uinput.lower() == 'startstop wc':
            fname = f"output_{counter}.csv"
            start_stop_weened_cont(filename=fname)
            counter += 1
        elif uinput.lower() == 'read sa':
            adc_reada()
        elif uinput.lower() == 'sweepdac':
            sweep_dac()
        elif uinput.lower() == 'setdac':
            set_dac()
        elif uinput.lower() == 'adcrate':
            set_adc_rate()
        elif uinput.lower() == 'sweepadcdac':
            fname = input("filename to write to (with .csv)\n")
            adc_dac_sweep(nons=nons, shunted=shunted, refer=refer, filename=fname)
        elif uinput.lower() == 'exit':
            print("Exiting...")
            break
        else:
            print(f"Unrecognized command: {uinput}")

if __name__ == "__main__":
    main()
