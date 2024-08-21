import subprocess
import time
import os

def is_watchdog_running():
    # Check if watchdog.py is running
    result = subprocess.run(['pgrep', '-f', 'watchdog_server.py'], stdout=subprocess.PIPE)
    return result.returncode == 0  # Returns True if watchdog.py is found running

def get_next_log_filename():
    # Ensure the output_log directory exists
    if not os.path.exists('output_log'):
        os.makedirs('output_log')
    
    # Get a count of the existing log files
    log_files = os.listdir('output_log')
    log_count = len(log_files)
    
    # Generate a new log filename based on the count
    return f'output_log/watchdog_server_log_{log_count + 1}.log'

def start_watchdog():
    # Generate a unique log filename
    log_filename = get_next_log_filename()
    
    # Redirect stdout and stderr to the log file
    with open(log_filename, 'a') as log_file:
        subprocess.Popen(['python3', 'watchdog_server.py'], stdout=log_file, stderr=log_file)

def monitor_watchdog():
    while True:
        try:
            if not is_watchdog_running():
                print("watchdog is not running. Starting it now...")
                start_watchdog()
            else:
                print("watchdog is already running.")
            
            time.sleep(30)  # Wait for 2 minutes
        except:
            time.sleep(30) 
            continue

if __name__ == "__main__":
    monitor_watchdog()
