from watchdog_server import Watchdog
import time
import socket

def register_function(name, watchdog_ip="127.0.0.1", watchdog_port=5006):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((watchdog_ip, watchdog_port))
        s.sendall(name.encode())

def main():
    # Start the watchdog
    watchdog = Watchdog()

    # Wait for the TCP server to be ready
    watchdog.tcp_server_ready.wait()

    # Register classes with the watchdog
    for name in ["ADS", "OPV", "QuadMag"]:
        register_function(name)

    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
