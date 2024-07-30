from ublox_gps import UbloxGps
import serial
import pynmea2
import time
#import trigger_mag_io


def gps_scan(gps_data):
    port = serial.Serial('/dev/ttyAMA0', baudrate=38400, timeout=1)
    gps = UbloxGps(port)
    print("GPS SCAN entered")

    try:
        nmea = gps.stream_nmea()
        print("CTF: ", nmea)
        parse(nmea, gps_data)
    except (ValueError, IOError) as err:
        print(f"failed")
        with open("sensor_log.txt", "a", newline='') as file:
            file.write("GPS ------ GPS scan failed"+ "\n")
        print(err)
    print(gps_data)
    time.sleep(10)

    


def parse(nmea_sentence, gps_data):
    nmea_msg = pynmea2.parse(nmea_sentence)
    print("Parsed: ", nmea_msg)
    if nmea_sentence.startswith('$GNGGA'):
        

        latitude = nmea_msg.latitude
        if lattiude == None:
            latitude = 0
        longitude = nmea_msg.longitude
        if longitude == None:
            longitude = 0
        altitude = nmea_msg.altitude
        if altitude == None:
            altitude = 0
        ns = nmea_msg.lat_dir
        if ns == None:
            ns = 'N'
        ew = nmea_msg.lon_dir
        if ew == None:
            ew = 'E'
        fix_quality = nmea_msg.gps_qual

        if gps_data['fix'] == 1 and fix_quality == 0:
            with open("gps_log.txt", "a", newline='') as file:
                file.write("Time HHMMSS - " + str(gps_data['timestamp']) +  " - " + "GPS ------ GPS fix lost"+ "\n")
        elif gps_data['fix'] == 0 and fix_quality == 1:
            with open("gps_log.txt", "a", newline='') as file:
                file.write("Time HHMMSS - " + str(gps_data['timestamp']) +  " - " + "GPS ------ GPS fix obtained"+ "\n") 

        gps_data['fix'] = fix_quality
        if fix_quality == 0:
            return

        timestamp = nmea_msg.timestamp
        #print("GPS time: ", timestamp)
        if timestamp == None:
            timestamp = '000000'

        gps_data['timestamp'] = timestamp
        #print("current time looks like: ", timestamp)
        gps_data['latitude'] = lattiude
        gps_data['longitude'] = longitude
        gps_data['altitude'] = altitude
        gps_data['ns_indicator'] = ns
        gps_data['ew_indicator'] = ew
        




    elif nmea_sentence.startswith('$GNVTG'):
        ground_speed = nmea_msg.spd_over_grnd_kmph
        if ground_speed == None:
            ground_speed = 0
        gps_data['ground_speed'] = ground_speed

    elif nmea_sentence.startswith('$GNGSV'):
        if isinstance(nmea_msg, pynmea2.types.talker.GSV):
            snr = 9
            # for sv in nmea_msg.sv_data:
            #     # process satellite data
            #     snr = sv
            #     break
        gps_data['snr'] = nmea_sentence
        

    else:
        #print("shouldn't be here")
        return