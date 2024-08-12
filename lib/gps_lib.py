import os
import serial
from serial import Serial
import time
from pyubx2 import UBXReader, UBXMessageError, UBXParseError
import pyubx2

class GPSScanner:
    def __init__(self, rtc):
        self.gps_data = {
            'timestamp': '000000',
            'latitude': 0,
            'longitude': 0,
            'ns_indicator': 'N',
            'ew_indicator': 'E',
            'altitude': 0,
            'fix': 0,
            'snr': 0,
            'num_sv': 0
        }
        self.posflag = False
        self.snrflag = False
        self.snr_vals = []
        
        self.line_count = 0
        self.current_file = None
        self.ensure_directory_exists()
        self.open_new_log_file()
        self.RTC = rtc
    
    def ensure_directory_exists(self):
        if not os.path.exists("gps_data"):
            os.makedirs("gps_data")
    
    def get_next_filename(self):
        files = [f for f in os.listdir("gps_data") if os.path.isfile(os.path.join("gps_data", f))]
        next_file_index = len(files)
        return os.path.join("gps_data", f"{next_file_index}_gps.txt")
    
    def open_new_log_file(self):
        if self.current_file:
            self.current_file.close()
        filename = self.get_next_filename()
        self.current_file = open(filename, "w", newline='')
        self.line_count = 0
    
    def write_to_log(self, message):
        self.current_file.write(message)
        self.current_file.write("\n")
        self.line_count += 1
        if self.line_count >= 1000:
            self.open_new_log_file()
    
    def gps_scan(self):
        try:
            stream = Serial('/dev/ttyACM0', baudrate=38400, timeout=1)  # Adjust port as needed
            self.write_to_log("GPS SCAN ENTERED")
            ubr = UBXReader(stream, protfilter=pyubx2.UBX_PROTOCOL + pyubx2.NMEA_PROTOCOL)
            while True:
                time.sleep(5)  # Update GPS data once every x seconds
                stream.reset_input_buffer()  # Clear stale messages from the sleep period
                starttime = time.time()
                self.posflag = False
                self.snrflag = False
                self.snr_vals = []
                while time.time() - starttime < 5:  # Scan for a maximum of x seconds
                    try:
                        raw_data, parsed_data = ubr.read()  # Read from GPS
                        if parsed_data:
                            self.update_gps_data(parsed_data)
                            if self.posflag and self.snrflag:
                                break  # Once valid data is received, sleep until next update interval
                    except (UBXMessageError, UBXParseError) as e:
                        self.write_to_log(f"UBX Error: {e} {parsed_data} {raw_data}")
                    except Exception as e:
                        self.write_to_log(f"Unknown Error: {e} {parsed_data} {raw_data}")
                    self.write_to_log(f"raw: {raw_data}, parsed: {parsed_data}")
        except (ValueError, IOError, serial.SerialException) as err:
            print(f"Failed to read GPS data: {err} {parsed_data}")
            self.write_to_log(f"GPS scan failed: {err}")

    def set_rtc_from_gps(self, rtc, parsed_data):
        """
        Sets the RTC time if a valid GPS time is found in the parsed_data.
        This function should be called when the GPS data is parsed.
        
        :param rtc: The RTC object (e.g., RV_8803 instance)
        :param parsed_data: The parsed GPS data
        """
        if parsed_data.identity == 'GNGGA' and parsed_data.time is not None:
            # Extract hours, minutes, and seconds from the parsed GPS time
            gps_time = parsed_data.time
            hours = int(gps_time[:2])
            minutes = int(gps_time[2:4])
            seconds = int(gps_time[4:6])
            
            # Set the RTC time using the extracted time
            rtc.setTime([seconds, minutes, hours])
            print(f"RTC time set to {hours:02d}:{minutes:02d}:{seconds:02d} based on GPS time.")

    
    def update_gps_data(self, parsed_data):
        if parsed_data.identity == 'GNGGA' and not self.posflag:
            latitude = parsed_data.lat if parsed_data.lat is not None else 0
            longitude = parsed_data.lon if parsed_data.lon is not None else 0
            altitude = parsed_data.alt if parsed_data.alt is not None else 0
            ns = parsed_data.NS if parsed_data.NS is not None else 'N'
            ew = parsed_data.EW if parsed_data.EW is not None else 'E'
            fix_quality = parsed_data.quality if parsed_data.quality is not None else 0
            timestamp = parsed_data.time if parsed_data.time is not None else '000000'
            self.gps_data['timestamp'] = timestamp
            self.set_rtc_from_gps(self.RTC, parsed_data)
            if self.gps_data['fix'] == 0 and fix_quality == 1:
                self.write_to_log(f"GPS FIX RECEIVED AT: {parsed_data}")
            elif self.gps_data['fix'] == 1 and fix_quality == 0:
                self.write_to_log(f"GPS FIX LOST AT: {parsed_data}")
            self.gps_data['fix'] = fix_quality
            if fix_quality == 0:  # If no fix, the read was not successful
                return
            self.write_to_log(str(parsed_data))  # Log NMEA string only if there is a fix (otherwise it is useless)
            self.gps_data['latitude'] = latitude
            self.gps_data['longitude'] = longitude
            self.gps_data['altitude'] = altitude
            self.gps_data['ns_indicator'] = ns
            self.gps_data['ew_indicator'] = ew
            self.posflag = True
        elif parsed_data.identity == 'GPGSV' and not self.snrflag:
            num_sv = parsed_data.numSV if parsed_data.numSV is not None else 0
            msg_num = parsed_data.msgNum if parsed_data.msgNum is not None else 0
            if num_sv == 0 or msg_num == 0:
                return
            if self.gps_data['fix'] == 1:
                self.write_to_log(str(parsed_data))
            num_read = 4
            if msg_num == 1:
                self.snr_vals = []
            if (num_sv - (msg_num - 1) * 4) <= 4:
                num_read = num_sv - (msg_num - 1) * 4
                self.snrflag = True
            if num_read >= 1 and parsed_data.cno_01:
                self.snr_vals.append(int(parsed_data.cno_01))
            if num_read >= 2 and parsed_data.cno_02:
                self.snr_vals.append(int(parsed_data.cno_02))
            if num_read >= 3 and parsed_data.cno_03:
                self.snr_vals.append(int(parsed_data.cno_03))
            if num_read >= 4 and parsed_data.cno_04:
                self.snr_vals.append(int(parsed_data.cno_04))
            if num_read > 4:
                print("ERROR, NUMREAD OVER 4")
            if self.snrflag:
                self.snr_vals.sort(reverse=True)
                total = sum(self.snr_vals[:min(len(self.snr_vals), 4)])
                numsats = min(len(self.snr_vals), 4)
                self.gps_data['snr'] = total / numsats if numsats > 0 else 0
                self.gps_data['num_sv'] = num_sv
        # Add other parsed_data.identities as needed

if __name__ == "__main__":
    gps_scanner = GPSScanner()
    gps_scanner.gps_scan()
