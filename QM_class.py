from Flight_GetQMData import QuadMag
import os
import glob
import numpy as np
import pandas as pd
import threading

class QuadMag():
    def __init__(self):
        self.qm_thread = threading.Thread(target=self.RunQM) #Create the thread object this runs off of the
        self.qm_thread.start()  

    def RunQM(self, prefix):
        i = 1
        while 1:
            #37 HZ CYCLE- Set sample rate, update name, run
            QuadMag.setSampleRate(37)
            name = prefix+"_"+str(i)+"_37Hz"
            QuadMag.setfilename(name)
            QuadMag.CollectData(0) #Change to 1 if raw

            #75 HZ CYCLE- Set sample rate, update name, run
            QuadMag.setSampleRate(75)
            name = prefix+"_"+str(i)+"_75Hz"
            QuadMag.setfilename(name)
            QuadMag.CollectData(0) #Change to 1 if raw
            i = i+1
        return

    def QuadMagBeaconator(self, QuadMag, BeacFreq):
        #BeacFreq = Beacon Frequency in Hz. Yes this will probably be less than 1Hz
        #Find folder, sort data by recent, get newest first
        folder_path = 'data_storage/'
        files = glob.glob(os.path.join(folder_path, '*'))
        files.sort(key=os.path.getmtime, reverse=True)
        if files[1]:
            beaconfile = files[1]
        else: beaconfile = files[0]
        df = pd.read_csv(beaconfile)
        height = df.shape[0]-1
        
        N_Beacons = int(QuadMag.getCollectionTime()*BeacFreq)
        steplength = int(np.floor(height/N_Beacons))
        extra_rows = len(df) % N_Beacons

        beacons = pd.DataFrame(columns = df.columns)
        i = 0
        startidx = 1
        for i in range(N_Beacons):
            newrow = [None]*len(df.columns)
            endidx = startidx+steplength
            chunk = df.iloc[startidx:endidx]
            for j in range(len(df.columns)):
                if j < 2:
                    q = chunk.iloc[1,j]
                    newrow[j]  = q
                else:
                    q = (chunk.iloc[:,j].mean())
                    newrow[j] = q
            beacons.loc[len(beacons.index)] = newrow 
            startidx = endidx
        return beacons