import serial
from serial import Serial
import time
from pyubx2 import UBXReader, UBXMessageError, UBXParseError
import pyubx2

class GPSScanner:
    def __init__(self):
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
        with open("gps_log.txt", "w", newline='') as file:
            file.write("")
    
    def gps_scan(self):
        try:
            stream = Serial('/dev/ttyACM0', baudrate=38400, timeout=1)  # Adjust port as needed
            with open("gps_log.txt", "a", newline='') as file:
                file.write(f"GPS SCAN ENTERED\n")
            ubr = UBXReader(stream, protfilter=pyubx2.UBX_PROTOCOL + pyubx2.NMEA_PROTOCOL)
            while True:
                time.sleep(5)  # Update GPS data once every x seconds
                #stream.reset_input_buffer()  # Clear stale messages from the sleep period
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
                        with open("gps_log.txt", "a", newline='') as file:
                            file.write(f"UBX Error: {e} {parsed_data} {raw_data}\n")
                    except Exception as e:
                        with open("gps_log.txt", "a", newline='') as file:
                            file.write(f"Unknown Error: {e} {parsed_data} {raw_data}\n")
        except (ValueError, IOError, serial.SerialException) as err:
            print(f"Failed to read GPS data: {err} {parsed_data}")
            with open("gps_log.txt", "a", newline='') as file:
                file.write(f"GPS scan failed: {err}\n")
    
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
            if self.gps_data['fix'] == 0 and fix_quality == 1:
                with open("gps_log.txt", "a", newline='') as file:
                    file.write(f"GPS FIX RECEIVED AT: {parsed_data}\n")
            elif self.gps_data['fix'] == 1 and fix_quality == 0:
                with open("gps_log.txt", "a", newline='') as file:
                    file.write(f"GPS FIX LOST AT: {parsed_data}\n")
            self.gps_data['fix'] = fix_quality
            if fix_quality == 0:  # If no fix, the read was not successful
                return
            with open("gps_log.txt", "a", newline='') as file:
                file.write(str(parsed_data) + "\n")  # Log NMEA string only if there is a fix (otherwise it is useless)
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
                with open("gps_log.txt", "a", newline='') as file:
                    file.write(str(parsed_data) + "\n")
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
                total = sum(self.snr_vals[:min(len(self.snr_vals), 3)])
                numsats = min(len(self.snr_vals), 3)
                self.gps_data['snr'] = total / numsats if numsats > 0 else 0
                self.gps_data['num_sv'] = num_sv
        # Add other parsed_data.identities as needed

if __name__ == "__main__":
    gps_scanner = GPSScanner()
    gps_scanner.gps_scan()
