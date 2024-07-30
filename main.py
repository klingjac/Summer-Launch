import threading
import os
import time

from opv_interface import opv_loop

def main():
    opv_thread = threading.Thread(target=opv_loop)
    opv_thread.start()

    
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
