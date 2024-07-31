import serial
from serial import Serial
import time
from pyubx2 import UBXReader
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
        self.posflag = False # flags for each read
        self.snrflag = False
        self.snr_vals = [] # array to store snr values
        # clear gps log
        with open("gps_log.txt", "w", newline='') as file:
            file.write("")
    def gps_scan(self):
        try:
            stream = Serial('/dev/ttyACM0', baudrate=38400, timeout=1)  # Adjust port as needed
            with open("gps_log.txt", "a", newline='') as file:
                file.write(f"GPS SCAN ENTERED\n")
            ubr = UBXReader(stream)
            while True:
                time.sleep(5)  # Update GPS data once every x seconds
                stream.reset_input_buffer()  # Clear stale messages from the sleep period
                starttime = time.time()
                self.posflag = False  # Reset flags
                self.snrflag = False
                self.snr_vals = [] # Clear snr vals array
                while time.time() - starttime < 5:  # Scan for a maximum of x seconds
                    _, parsed_data = ubr.read()  # Read from GPS
                    #print(parsed_data)
                    self.update_gps_data(parsed_data)
                    if self.posflag and self.snrflag:  # Break once pos and snr are both updated
                        #print(self.gps_data)  # Print or process the updated GPS data
                        break  # Once valid data is received, sleep until next update interval
        except (ValueError, IOError, serial.SerialException) as err:
            print(f"Failed to read GPS data: {err}")
            with open("gps_log.txt", "a", newline='') as file:
                file.write(f"GPS ------ GPS scan failed: {err}\n")
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
                    file.write("GPS FIX RECEIVED AT: {parsed_data}\n")
            elif self.gps_data['fix'] == 1 and fix_quality == 0:
                with open("gps_log.txt", "a", newline='') as file:
                    file.write("GPS FIX LOST AT: {parsed_data}\n")
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
            if num_sv == 0 or msg_num == 0:  # No fix, so no satellites to read
                return
            if self.gps_data['fix'] == 1:
                with open("gps_log.txt", "a", newline='') as file:  # Log GPGSV message only if there is a fix
                    file.write(str(parsed_data) + "\n")
            num_read = 4
            if msg_num == 1:
                self.snr_vals = [] # make sure to clear snr_vals on the first message (new gsv chain in case of a failed chain or something else)
            if (num_sv - (msg_num - 1) * 4) <= 4:  # Number of reads in the current message
                num_read = num_sv - (msg_num - 1) * 4  # Number of reads
                self.snrflag = True  # If this condition is true, there are no more GPGSV messages in the current chain
            if num_read >= 1 and parsed_data.cno_01: # only add the value if it exists
                self.snr_vals.append(int(parsed_data.cno_01))
            if num_read >= 2 and parsed_data.cno_02:
                self.snr_vals.append(int(parsed_data.cno_02))
            if num_read >= 3 and parsed_data.cno_03:
                self.snr_vals.append(int(parsed_data.cno_03))
            if num_read >= 4 and parsed_data.cno_04:
                self.snr_vals.append(int(parsed_data.cno_04))
            if num_read > 4:
                print("ERROR, NUMREAD OVER 4")
            if self.snrflag:  # This was the last message in a chain
                self.snr_vals.sort(reverse = True) # sort the received snr values in descending order
                total = 0
                numsats = 0
                for i in range(0, min(len(self.snr_vals),3)): # includes the case where there are less than 3 snr values
                    numsats += 1
                    total += self.snr_vals[i]
                self.gps_data['snr'] = total/numsats if numsats > 0 else 0
                self.gps_data['num_sv'] = num_sv
        # add other parsed_data.identities as needed