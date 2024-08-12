import smbus
import time
RTC_ADDRESS = 0x32
MSEC_REG = 0x10
SEC_REG = 0x00
MIN_REG = 0x01
HOUR_REG = 0x02
WKDAY_REG = 0x03
DATE_REG = 0x04
MONTH_REG = 0x05
YEAR_REG = 0x06
class RV_8803():
    def __init__(self, smbus_num = 2):
        self.i2c_bus_num = smbus_num
        self.bus = smbus.SMBus(smbus_num)
    def timeFormat(self, timeArray):
        """
        Takes list of ints, and ints.
        Converts input to bytes, removes byte markers, and add 0s if converted byte string is single character
        """
        if type(timeArray) is list:
            timeList = [hex(x)[2:] for x in timeArray]
            for i in range(len(timeList)):
                x = timeList[i]
                if len(x) == 1:
                    timeList[i] = '0'+x
            return timeList
        elif type(timeArray) is int:
            timeString = hex(timeArray)[2:]
            if len(timeString) == 1:
                timeString = '0'+timeString
            return timeString
        else:
            return None
    ### GET FUNCTIONS ###
    def getFullTime(self):
        """
        Gets full time string in the form DD/MM/YY - HH/MM/SS
        """
        t = self.getTime()
        d = self.getCalendar()
        return d+' - '+t
    def getTime(self):
        """
        Gets time. Returns time in format HH:mm:SS
        """
        # Read 3 bytes from RTC starting from seconds register. Returns list of ['ss', 'mm', 'hh']. Register automatically increments every read/write
        timeRead = self.bus.read_i2c_block_data(RTC_ADDRESS, MSEC_REG, 4)
        # Flips list in correct order, and does some formatting
        timeList = self.timeFormat(timeRead[::-1])
        # Joins seconds and miliseconds
        timeList[2] = timeList[2]+'.'+timeList[3]
        timeList = timeList[:-1]
        timeString = ':'.join(timeList)
        return timeString
    def getCalendar(self):
        """
        Gets calendar date. Returns date in format DD/MM/YY
        """
        timeRead = self.bus.read_i2c_block_data(RTC_ADDRESS, DATE_REG, 3)
        timeList = self.timeFormat(timeRead)
        timeString = '/'.join(timeList)
        return timeString
    def getSeconds(self):
        """
        Gets seconds. Returns string in XX format.
        All single 'get' functions below can be combined into a single function. They are separated into individual functions to be user-friendly
        """
        # Reads single byte from RTC
        timeRead = self.bus.read_byte_data(RTC_ADDRESS, SEC_REG)
        timeString = self.timeFormat(timeRead)
        return timeString
    def getMiliseconds(self):
        timeRead = self.bus.read_byte_data(RTC_ADDRESS, MSEC_REG)
        timeString = self.timeFormat(timeRead)
        return timeString
    def getMinutes(self):
        timeRead = self.bus.read_byte_data(RTC_ADDRESS, MIN_REG)
        timeString = self.timeFormat(timeRead)
        return timeString
    def getHours(self):
        timeRead = self.bus.read_byte_data(RTC_ADDRESS, HOUR_REG)
        timeString = self.timeFormat(timeRead)
        return timeString
    def getWeekday(self):
        timeRead = self.bus.read_byte_data(RTC_ADDRESS, WKDAY_REG)
        timeString = self.timeFormat(timeRead)
        return timeString
    def getDate(self):
        timeRead = self.bus.read_byte_data(RTC_ADDRESS, DATE_REG)
        timeString = self.timeFormat(timeRead)
        return timeString
    def getMonth(self):
        timeRead = self.bus.read_byte_data(RTC_ADDRESS, MONTH_REG)
        timeString = self.timeFormat(timeRead)
        return timeString
    def getYear(self):
        timeRead = self.bus.read_byte_data(RTC_ADDRESS, YEAR_REG)
        timeString = self.timeFormat(timeRead)
        return timeString
    ### SET FUNTIONS ###
    def checkTimeArray(self, array):
        """
        Checks whether values in time array are within allowable range
        Returns a list of booleans of same size, with T or F indicating whether the value at that index is within range
        """
        logicArray = []
        logicArray.append(True if (array[0]>=0 and array[0]<=59) else False)
        logicArray.append(True if (array[1]>=0 and array[1]<=59) else False)
        logicArray.append(True if (array[2]>=0 and array[2]<=23) else False)
        return logicArray
    def checkCalendarArray(self, array):
        logicArray = []
        logicArray.append(True if (array[0]>=1 and array[0]<=31) else False)
        logicArray.append(True if (array[1]>=1 and array[1]<=12) else False)
        logicArray.append(True if (array[2]>=2000 and array[2]<=2099) else False)
        return logicArray
    def checkFullArray(self, array):
        logicArr1 = self.checkTimeArray(array[:3])
        logicArr2 = self.checkCalendarArray(array[4:])
        logicArray = logicArr1 + logicArr2
        if (array[3]>=1 and array[3]<=7):
            logicArray.insert(3, True)
        else:
            logicArray.insert(3, False)
        return logicArray
    def setFullTime(self, timeArray):
        """
        Sets all time registers. Argument must be in form shown below
        """
        if type(timeArray) is not list:
            print("Argument not list. Need a list of 7 integers in form [{seconds}, {minutes}, {hours}, {weekday (1-7, 1 is Sunday)}, {day}, {month}, {year}]")
            return None
        elif len(timeArray) != 7:
            print("Wrong length. Need a list of 7 values")
            return None
        for x in timeArray:
            if type(x) is not int:
                print("Time values can only be integers")
                return None
        logicArray = self.checkFullArray(timeArray)
        for x in logicArray:
            if not x:
                print("Value(s) in \"FALSE\" index(s) is out of allowable range")
                print(logicArray)
                return None
        timeArray = [int(str(x),16) for x in timeArray]
        self.bus.write_block_data(RTC_ADDRESS, MSEC_REG, timeArray)
        return None
    def setTime(self, timeArray):
        """
        Sets time register. Argument must be in form shown below
        """
        if type(timeArray) is not list:
            print("Argument not list. Need a list of 3 integers in form [{seconds}, {minutes}, {hours}]")
            return None
        elif len(timeArray) != 3:
            print("Wrong length. Need a list of 3 values")
            return None
        for x in timeArray:
            if type(x) is not int:
                print("Time values can only be integers")
                return None
        logicArray = self.checkTimeArray(timeArray)
        for x in logicArray:
            if not x:
                print("Value(s) in \"FALSE\" index(s) is out of allowable range")
                print(logicArray)
                return None
        timeArray = [int(str(x),16) for x in timeArray]
        self.bus.write_block_data(RTC_ADDRESS, MSEC_REG, timeArray)
        return None
    def setCalendar(self, timeArray):
        """
        Sets all calendar registers. Argument must be in form shown below
        """
        if type(timeArray) is not list:
            print("Argument not list. Need a list of 3 integers in form [{day}, {month}, {year}]")
            return None
        elif len(timeArray) != 3:
            print("Wrong length. Need a list of 3 values")
            return None
        for x in timeArray:
            if type(x) is not int:
                print("Time values can only be integers")
                return None
        logicArray = self.checkCalendarArray(timeArray)
        for x in logicArray:
            if not x:
                print("Value(s) in \"FALSE\" index(s) is out of allowable range")
                print(logicArray)
                return None
        timeArray = [int(str(x),16) for x in timeArray]
        self.bus.write_block_data(RTC_ADDRESS, WKDAY_REG, timeArray)
        return None
    def setSeconds(self, val):
        """
        All functions below are to set individual time registers
        """
        if type(val) is not int:
            print("Time value can only be integer")
            return None
        if val<0 or val>59:
            print("Must be between 0-59s")
            return None
        val = int(str(val),16)
        self.bus.write_byte_data(RTC_ADDRESS, SEC_REG, val)
        return None
    def setMinutes(self, val):
        if type(val) is not int:
            print("Time value can only be integer")
            return None
        if val<0 or val>59:
            print("Must be between 0-59m")
            return None
        val = int(str(val),16)
        self.bus.write_byte_data(RTC_ADDRESS, MIN_REG, val)
        return None
    def setHours(self, val):
        if type(val) is not int:
            print("Time value can only be integer")
            return None
        if val<0 or val>23:
            print("Must be between 0-23 hours")
            return None
        val = int(str(val),16)
        self.bus.write_byte_data(RTC_ADDRESS, HOUR_REG, val)
        return None
    def setWeekday(self, val):
        if type(val) is not int:
            print("Time value can only be integer")
            return None
        if val<1 or val>7:
            print("Must be between 1-7. 1 is Sunday")
            return None
        val = int(str(val),16)
        self.bus.write_byte_data(RTC_ADDRESS, WKDAY_REG, val)
        return None
    def setDate(self, val):
        if type(val) is not int:
            print("Time value can only be integer")
            return None
        if val<1 or val>31:
            print("Must be between 1-31")
            return None
        val = int(str(val),16)
        self.bus.write_byte_data(RTC_ADDRESS, DATE_REG, val)
        return None
    def setMonth(self, val):
        if type(val) is not int:
            print("Time value can only be integer")
            return None
        if val<1 or val>12:
            print("Must be between 1-12")
            return None
        val = int(str(val),16)
        self.bus.write_byte_data(RTC_ADDRESS, MONTH_REG, val)
        return None
    def setYear(self, val):
        if type(val) is not int:
            print("Time value can only be integer")
            return None
        if val<2000 or val>2099:
            print("Must be between 2000-2099")
            return None
        val = int(str(val),16)
        self.bus.write_byte_data(RTC_ADDRESS, YEAR_REG, val)
        return None