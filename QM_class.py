from Flight_GetQMData import QuadMag
import os
import glob
import numpy as np
import pandas as pd

class QuadMag_logger:
    def __init__(self, heartbeat):
        self.QuadMag = QuadMag()
        self.QuadMag.setCollectionTime(20)
        self.running = True
        self.heartbeat = heartbeat

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

            self.heartbeat.value = True  # Update heartbeat

    def run(self):
        self.RunQM()

def run_quadmag(heartbeat):
    logger = QuadMag_logger(heartbeat)
    logger.run()

if __name__ == "__main__":
    heartbeat = create_shared_heartbeat()
    run_quadmag(heartbeat)
