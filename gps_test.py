from gps_lib import gps_scan
import threading

gps_data = {
    'timestamp': '000000',  # HHMMSS format
    'latitude': 0,
    'longitude': 0,
    'ns_indicator': 'N',
    'ew_indicator': 'E',
    'ground_speed': 0,
    'altitude': 0,
    'snr': 0,
    'fix': 0
}


thread = threading.Thread(target=gps_scan, args=(gps_data,))
thread.start()