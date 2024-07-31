import threading
import socket
import time

class Watchdog:
    def __init__(self, udp_ip="127.0.0.1", udp_port=5005, tcp_ip="127.0.0.1", tcp_port=5006):
        self.udp_ip = udp_ip
        self.udp_port = udp_port
        self.tcp_ip = tcp_ip
        self.tcp_port = tcp_port
        self.last_heartbeat = {}
        self.threads = {}
        self.lock = threading.Lock()

        # Start the TCP server for registration
        self.tcp_server_thread = threading.Thread(target=self.tcp_server, daemon=True)
        self.tcp_server_thread.start()

        # Start the UDP listener for heartbeats
        self.udp_listener_thread = threading.Thread(target=self.udp_listener, daemon=True)
        self.udp_listener_thread.start()

        # Start the watchdog monitor
        self.watchdog_thread = threading.Thread(target=self.watchdog, daemon=True)
        self.watchdog_thread.start()

    def tcp_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.tcp_ip, self.tcp_port))
            s.listen()
            while True:
                conn, addr = s.accept()
                with conn:
                    data = conn.recv(1024)
                    if data:
                        name = data.decode()
                        print(f"Registered {name}")
                        with self.lock:
                            self.start_thread(name)

    def start_thread(self, name):
        thread = threading.Thread(target=self.target_function, args=(name,), daemon=True)
        self.threads[name] = thread
        thread.start()
        self.last_heartbeat[name] = time.time()
        print(f"Started thread {name}")

    def target_function(self, name):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            while True:
                message = f"heartbeat from {name}"
                sock.sendto(message.encode(), (self.udp_ip, self.udp_port))
                time.sleep(10)  # Send a heartbeat every 10 seconds

    def udp_listener(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind((self.udp_ip, self.udp_port))
            while True:
                data, addr = sock.recvfrom(1024)
                message = data.decode()
                name = message.split()[-1]  # Extract the thread name from the message
                with self.lock:
                    self.last_heartbeat[name] = time.time()
                print(f"Received heartbeat from {name}")

    def watchdog(self):
        while True:
            current_time = time.time()
            with self.lock:
                for name, last_time in list(self.last_heartbeat.items()):
                    if current_time - last_time > 60:
                        print(f"{name} failed to send heartbeat. Restarting...")
                        self.restart_thread(name)
            time.sleep(5)  # Check every 5 seconds

    def restart_thread(self, name):
        self.threads[name].join()
        self.start_thread(name)
        print(f"Restarted thread {name}")

# Example usage
if __name__ == "__main__":
    watchdog = Watchdog()

    # Simulate registering target functions
    def register_function(name):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((watchdog.tcp_ip, watchdog.tcp_port))
            s.sendall(name.encode())

    # Register 3 target functions
    for i in range(3):
        register_function(f"thread-{i}")

    # Keep the main thread alive
    while True:
        time.sleep(1)
