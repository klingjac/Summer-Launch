import threading
import time
from gps_lib import GPSScanner
# Initialize the GPSScanner object
gps_scanner = GPSScanner()
# Create a thread for the gps_scan method
thread = threading.Thread(target=gps_scanner.gps_scan)
# Start the thread
thread.start()
# Periodically read and print the GPS data
try:
    while True:
        time.sleep(10)
        print(gps_scanner.gps_data)  # Reads and prints GPS data every 10 seconds
except KeyboardInterrupt:
    print("Stopping GPS scan.")
    thread.join()