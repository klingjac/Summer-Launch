import threading
from Flight_GetQMData import QuadMag
import os
import glob
import numpy as np
import pandas as pd

class QuadMag_logger:
    def __init__(self):
        self.QuadMag = QuadMag()
        self.QuadMag.setCollectionTime(20)
        self.running = True
        self.alive_flag = threading.Event()
        self.alive_flag.set()

    def RunQM(self):
        prefix = "test"
        i = 1
        while self.running:
            # 37 HZ CYCLE
            self.QuadMag.setSampleRate(37)
            name = f"{prefix}_{i}_37Hz"
            self.QuadMag.setfilename(name)
            self.QuadMag.CollectData(0)

            # 75 HZ CYCLE
            self.QuadMag.setSampleRate(75)
            name = f"{prefix}_{i}_75Hz"
            self.QuadMag.setfilename(name)
            self.QuadMag.CollectData(0)
            i += 1

            self.alive_flag.set()  # Update alive flag

    def run(self):
        self.RunQM()
        # try:
        #     self.RunQM()
        # except Exception as e:
        #     self.alive_flag.clear()
        #     print(f"Exception in QuadMag logger: {e}")

