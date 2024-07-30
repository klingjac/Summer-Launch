import os
import time
from FlightBoard import start_stop_weened

def generate_opv_file_name(directory):
    
    num_files = len([f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))])
    
    unix_time = int(time.time())
    
    file_name = f"{num_files}_{unix_time}.csv"
    return os.path.join(directory, file_name)

def opv_loop():
    directory = "./OPV"
    os.makedirs(directory, exist_ok=True)
    while True:
        #Send ping via UDP client
        file_path = generate_opv_file_name(directory)
        print(file_path)
        start_stop_weened(file_path)
        # Sleep for a certain period if needed to avoid excessive looping
        time.sleep(0.1) 

