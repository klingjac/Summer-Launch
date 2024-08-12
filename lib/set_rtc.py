from RTC_Driver import RV_8803  # Assuming the class is saved in a file named RTC_Driver.py
import time
import datetime

def main():
    # Initialize the RTC module (adjust the smbus number if needed)
    rtc = RV_8803(smbus_num=2)

    # Get the current time in UTC
    now = datetime.datetime.utcnow()
    
    # Create a time array in the format: [seconds, minutes, hours, weekday (1-7, Sunday=1), day, month, year]
    time_array = [
        now.second,
        now.minute,
        now.hour,
        now.isoweekday() % 7 + 1,  # Convert isoweekday (1=Monday, 7=Sunday) to weekday (1=Sunday, 7=Saturday)
        now.day,
        now.month,
        now.year
    ]
    print(f"time array : {time_array}")
    
    # Set the RTC time using the time array
    rtc.setFullTime(time_array)
    print(f"RTC time {rtc.getFullTime()}")
    
    print("RTC time has been set successfully to the Raspberry Pi system time (UTC).")

if __name__ == "__main__":
    main()
