from pickle import TRUE
import numpy as np
import pandas as pd
from scipy import signal

fix_char = '' #vcoi #TODO fix issue that arises with time array from first data point being removed i.e. set to nan

class quad_data_frame :
    def __init(self) :
        self.c = np.array()
        self.p = pd.DataFrame() #x,y,z,b pni axis/total field
        self.t = pd.DataFrame() #t,t,t,t timestamps for each axis
        self.td = pd.DataFrame() #td,td,td,td period between each measurement
        self.im = pd.DataFrame() #ax, ay, az, gx, gy, gz imu accelerometer/gyroscope
        self.tt = pd.DataFrame() #temperature 
        self.sr = 0 #sampling rate 
        self.cc = 0 #cycle count
        self.os = 1 #oversamples
        self.mn = -1

    def update_self(self) :
        #updates the calculated b field and sampling rate if the values of x,y,z or t have changed
        
        self.c[0].update_self()
        x = self.c[0].p.iloc[:, 0]
        y = self.c[0].p.iloc[:, 1]
        z = self.c[0].p.iloc[:, 2]
        t = self.c[0].t.iloc[:, 0]
        for i in range(1, len(self.c)) :
            self.c[i].update_self()
            x = x.add(self.c[i].p.iloc[:, 0])
            y = y.add(self.c[i].p.iloc[:, 1])
            z = z.add(self.c[i].p.iloc[:, 2])
            t = t.add(self.c[i].t.iloc[:, 0])
        
        #remove the offsets
        #
        #for i in range (0, len(self.c)) :
        #    x = x.sub(self.c[i].offset[0]) 
        #    y = y.sub(self.c[i].offset[1])
        #    z = z.sub(self.c[i].offset[2])

        x = x.div(4.0)
        y = y.div(4.0)
        z = z.div(4.0)
        t = t.div(4.0)

        b = x.pow(2)+y.pow(2)+z.pow(2) #bpni readings
        b = b.pow(0.5)

        tx = t.to_numpy()[1:]
        ty = t.to_numpy()[:-1]
        tz = tx - ty
        td = pd.Series(tz)
        self.p = pd.DataFrame({'0': x,'1':y,'2': z,'3': b})
        self.t = pd.DataFrame({'0': t, '1':t, '2':t, '3':t})
        self.td = pd.DataFrame({'0': td,'1': td,'2': td,'3': td})
        self.sr = 1/(td.mean())

class pni_data_frame :
    def __init(self) :
        self.p = pd.DataFrame() #x,y,z,b pni axis/total field
        self.t = pd.DataFrame() #t,t,t,t timestamps for each axis
        self.td = pd.DataFrame() #td,td,td,td period between each measurement
        self.sr = 0 #sampling rate 
        self.cc = 0 #cycle count
        self.os = 1 #oversamples
        self.mn = 0 #mag identification number
        self.offset = [0, 0, 0] #just 3 offset values for x,y,z

    def update_self(self) :
        #updates the calculated b field and sampling rate if the values of x,y,z or t have changed

        self.calc_offset()

        self.t = self.t.sub(self.t.iloc[0])
        x = self.p.iloc[:, 0].sub(self.offset[0])
        y = self.p.iloc[:, 1].sub(self.offset[1])
        z = self.p.iloc[:, 2].sub(self.offset[2])

        b = x.pow(2)+y.pow(2)+z.pow(2) #bpni readings
        b = b.pow(0.5)

        tx = self.t.iloc[:,0].to_numpy()[1:]
        ty = self.t.iloc[:,0].to_numpy()[:-1]
        tz = tx - ty
        td = pd.Series(tz)
        self.p = pd.DataFrame({'0': x,'1': y,'2': z,'3': b})
        self.td = pd.DataFrame({'0': td,'1': td,'2': td,'3': td})
        self.sr = 1/(td.mean())

    def fix_self(self) :
        #fixes the datasets of this pni data frame
        a = fix_pni_dataset(self.t.iloc[:,0], self.p.iloc[:,0], fix_char)
        b = fix_pni_dataset(self.t.iloc[:,1], self.p.iloc[:,1], fix_char)
        c = fix_pni_dataset(self.t.iloc[:,2], self.p.iloc[:,2], fix_char)
        d = fix_pni_dataset(self.t.iloc[:,3], self.p.iloc[:,3], fix_char)
        self.t = pd.DataFrame({'0': a[0],'1':b[0],'2': c[0],'3': d[0]})
        self.p = pd.DataFrame({'0': a[1],'1':b[1],'2': c[1],'3': d[1]})
        self.update_self() #workaround for subtracting mean but not affecting quad data set

    def calc_offset(self) :
        #calculates the offset as the mean of the measured field
        #NOTE: assumes that the field is 0nT accross all axis

        self.offset[1] = self.p.iloc[:,1].mean()
        self.offset[2] = self.p.iloc[:,2].mean()
        self.offset[0] = self.p.iloc[:,0].mean()

        #self.offset[0] = 0 #alternative hardcode method x 
        #self.offset[1] = 0 #alternative hardcode method y 
        #self.offset[2] = 0 #alternative hardcode method z 

def pni_file_decode_quad(fn) :
    # def: decodes file based on quad mag python code formatting into a data_frame object and returns it
    # in: string fn (file to read from), int mn (mag identification)
    # out: quad_data_frame populated with file contents 
    cdf = pd.read_csv(fn, skiprows=1, nrows=1, header=None)
    po = quad_data_frame()
    po.c = np.array([pni_data_frame(), pni_data_frame(), pni_data_frame(), pni_data_frame()]) #weird fix for bad python init
    po.cc = cdf.iloc[0,0]
    po.os = cdf.iloc[0,1]
    print("po.cc = " + po.cc + ", po.os = " + po.os)
    sf = float((1000/(0.3671 * po.cc + 1.5)) / po.os) #current accepted method
    #sf = float(1000/(0.3671 * cc * os + 1.5)) #alternative
    pdf = pd.read_csv(fn, skiprows=4, header=None) #read into pd dataframe, skipping file header and blank line

    #fix_corrupted_file(pdf)

    xtt = 0
    ytt = 0
    ztt = 0

    t = pdf.iloc[:,1]
    t = t.sub(t.iloc[0]) # start time from zero
    x = pdf.iloc[:,2].multiply(sf) #xpni readings
    xtt = x
    y = pdf.iloc[:,3].multiply(sf) #ypni readings
    ytt = y
    z = pdf.iloc[:,4].multiply(sf) #zpni readings
    ztt = z
    b = x.pow(2)+y.pow(2)+z.pow(2) #bpni readings
    b = b.pow(0.5)

    tx = t.to_numpy()[1:]
    ty = t.to_numpy()[:-1]
    tz = tx - ty
    td = pd.Series(tz)
    po.c[0].t = pd.DataFrame({'0': t, '1':t, '2':t, '3':t})
    po.c[0].p = pd.DataFrame({'0': x,'1':y,'2': z,'3': b})
    po.c[0].td = pd.DataFrame({'0': td,'1': td,'2': td,'3': td})
    po.c[0].sr = 1/(td.mean())
    po.c[0].cc = po.cc
    po.c[0].os = po.os
    po.c[0].mn = 0
    po.c[0].offset = [0, 0, 0]
    po.c[0].calc_offset()

    x = pdf.iloc[:,5].multiply(sf) #xpni readings
    xtt = xtt.add(x)
    y = pdf.iloc[:,6].multiply(sf) #ypni readings
    ytt = ytt.add(y)
    z = pdf.iloc[:,7].multiply(sf) #zpni readings
    ztt = ztt.add(z)
    b = x.pow(2)+y.pow(2)+z.pow(2) #bpni readings
    b = b.pow(0.5)

    po.c[1].t = pd.DataFrame({'0': t, '1':t, '2':t, '3':t})
    po.c[1].p = pd.DataFrame({'0': x,'1':y,'2': z,'3': b})
    po.c[1].td = pd.DataFrame({'0': td,'1': td,'2': td,'3': td})
    po.c[1].sr = 1/(td.mean())
    po.c[1].cc = po.cc
    po.c[1].os = po.os
    po.c[1].mn = 1
    po.c[1].offset = [0, 0, 0]
    po.c[1].calc_offset()

    x = pdf.iloc[:,8].multiply(sf) #xpni readings
    xtt = xtt.add(x)
    y = pdf.iloc[:,9].multiply(sf) #ypni readings
    ytt = ytt.add(y)
    z = pdf.iloc[:,10].multiply(sf) #zpni readings
    ztt = ztt.add(z)
    b = x.pow(2)+y.pow(2)+z.pow(2) #bpni readings
    b = b.pow(0.5)

    po.c[2].t = pd.DataFrame({'0': t, '1':t, '2':t, '3':t})
    po.c[2].p = pd.DataFrame({'0': x,'1':y,'2': z,'3': b})
    po.c[2].td = pd.DataFrame({'0': td,'1': td,'2': td,'3': td})
    po.c[2].sr = 1/(td.mean())
    po.c[2].cc = po.cc
    po.c[2].os = po.os
    po.c[2].mn = 2
    po.c[2].offset = [0, 0, 0]
    po.c[2].calc_offset()
    
    x = pdf.iloc[:,11].multiply(sf) #xpni readings
    xtt = xtt.add(x)
    y = pdf.iloc[:,12].multiply(sf) #ypni readings
    ytt = ytt.add(y)
    z = pdf.iloc[:,13].multiply(sf) #zpni readings
    ztt = ztt.add(z)
    b = x.pow(2)+y.pow(2)+z.pow(2) #bpni readings
    b = b.pow(0.5)

    po.c[3].t = pd.DataFrame({'0': t, '1':t, '2':t, '3':t})
    po.c[3].p = pd.DataFrame({'0': x,'1':y,'2': z,'3': b})
    po.c[3].td = pd.DataFrame({'0': td,'1': td,'2': td,'3': td})
    po.c[3].sr = 1/(td.mean())
    po.c[3].cc = po.cc
    po.c[3].os = po.os
    po.c[3].mn = 3
    po.c[3].offset = [0, 0, 0]    
    po.c[3].calc_offset()

    #remove the offsets
    for i in range (0, 4) :
        xtt = xtt.sub(po.c[i].offset[0]) 
        ytt = ytt.sub(po.c[i].offset[1])
        ztt = ztt.sub(po.c[i].offset[2])

    xtt = xtt.div(4.0)
    ytt = ytt.div(4.0)
    ztt = ztt.div(4.0)
    b = xtt.pow(2)+ytt.pow(2)+ztt.pow(2) #bpni readings
    b = b.pow(0.5)

    po.t = pd.DataFrame({'0': t, '1':t, '2':t, '3':t})
    po.p = pd.DataFrame({'0': xtt,'1':ytt,'2': ztt,'3': b})
    po.td = pd.DataFrame({'0': td,'1': td,'2': td,'3': td})
    po.sr = 1/(td.mean())
    po.mn = 'quad'
    
    pni_describe(po)

    return po

def pni_file_decode_sean(fn, os, cc, mn) :
    # def: decodes file based on seans python code formatting into a data_frame object and returns it
    # in: string fn (file to read from), int os (number of oversamples), int cc (cycle count), int mn (mag identification)
    # out: pni_data_frame populated with file contents 
    cdf = pd.read_csv(fn, skiprows=2, nrows=1, header=None)
    po = pni_data_frame()
    po.cc = int(cdf.iloc[0,4])
    sf = float((1000/(0.3671 * po.cc + 1.5)) / os) #current accepted method
    #sf = float(1000/(0.3671 * po.cc * os + 1.5)) #alternative
    
    pdf = pd.read_csv(fn, skiprows=3, header=None) #read into pd dataframe, skipping file header
    t = pdf.iloc[:,0]
    x = pdf.iloc[:,1].multiply(sf) #xpni readings
    y = pdf.iloc[:,2].multiply(sf) #ypni readings
    z = pdf.iloc[:,3].multiply(sf) #zpni readings
    b = x.pow(2)+y.pow(2)+z.pow(2) #bpni readings
    b = b.pow(0.5)
    tx = t.to_numpy()[1:]
    ty = t.to_numpy()[:-1]
    tz = tx - ty
    td = pd.Series(tz)
    po.t = pd.DataFrame({'0': t, '1':t, '2':t, '3':t})
    po.p = pd.DataFrame({'0': x,'1':y,'2': z,'3': b})
    po.td = pd.DataFrame({'0': td,'1': td,'2': td,'3': td})
    po.sr = 1/(td.mean())
    po.os = os
    po.mn = mn
    po.offset = [0, 0, 0]    
    po.calc_offset()

    return po

def fix_pni_dataset(t, d, f):
    # def: removes outliers from your time series and data series based on f args/crops percentage of the data
    # in: panda series t (time series), panda series d (data series), string f (flags)
    # out: nothing
    # flags:
    #   'v' is verbose ie print whats happening
    #   'c' is crop ie chop first cper and last cper of data points       
    #   'o' is remove outliers
    #   'i' is interpolate data

    if f == '' :
        return [t,d]

    cper = 10.0 #change this to percent of data you want to remove from start and end of dataset

    ct = True if f.find('c') != -1 else False
    vt = True if f.find('v') != -1 else False
    ot = True if f.find('o') != -1 else False
    it = True if f.find('i') != -1 else False

    co = 0
    cl = d.size
    cp = int(cl * (cper/100.0))

    if ct :
        co = cp*2
        #d.iloc[:(cp+1)] = np.nan
        #d.iloc[(cl-cp):] = np.nan
        #t.iloc[:(cp+1)] = np.nan
        #t.iloc[(cl-cp):] = np.nan
        t = t.iloc[cp+1:cl-cp] #actually removes the datapoint now instead of nan
        d = d.iloc[cp+1:cl-cp]
        if vt :
            print("Removed data points (crop) 0 to " + str(cp) + " and data points (crop) " + str(cl-cp) + " to " + str(cl))


    dm = d.mean()
    ds = d.std()
    no = 0
    zdf = ((d.sub(dm)).div(ds)).abs()

    if vt and ot :
        for i,j in enumerate(zdf) :
            if j != np.nan and j > 4 : #outliers are > 4 std
                print("Removed data point (outlier) " + str(round(d.iloc[i],3)) + " at index " + str(i))
                t.iloc[i] = t.iloc[i] if it else np.nan
                d.iloc[i] = np.nan
                no+=1

    elif ot :
        for i,j in enumerate(zdf) :
            if j != np.nan and j > 4 : 
                t.iloc[i] = t.iloc[i] if it else np.nan
                d.iloc[i] = np.nan
                no+=1

    if it : #interpolate 
        #if ct:
        #    nsn, xx = nan_helper(d.iloc[cp+1:cl-cp].to_numpy()) #only interpolate data not cropped 
        #    d.iloc[cp+1:cl-cp][nsn]= np.interp(xx(nsn), xx(~nsn), d.iloc[cp+1:cl-cp][~nsn])
        #else :
        nsn, xx = nan_helper(d.to_numpy())
        d.iloc[nsn]= np.interp(xx(nsn), xx(~nsn), d.iloc[~nsn])

    if vt :
        print("\n***********************************************************")
        print("The mean of this data set before outlier removal was " + str(dm) + " with standard deviation " + str(ds))
        print("The mean of this data set after outlier removal is " + str(d.mean()) + " with standard deviation " + str(d.std()))
        print("\nRemoved " + str(no+co) + " data points out of " + str(cl) + " total")
        print("Removed " + str(no) + " outlier data points and cropped " + str(co) + " data points\n")
        print("***********************************************************\n")

    return [t,d]

def nan_helper(a) :
    #def:
    #in:
    #out:
    return np.isnan(a), lambda z: z.nonzero()[0]

def decimate_helper(do, dsr) :
    #def: decimates data to 1hz using scipy decimate function
    #in: do is pni data object, dsr is the sample rate desired (must be int factor of original sr or close to)
    #out: modified pni data object with updated dsr sample rate and corresponding data

    nt = pd.DataFrame()
    nd = pd.DataFrame()

    while(do.sr > float(dsr*4.0)) :
        a = pd.Series(signal.decimate(do.t.iloc[:,0], 2))
        b = pd.Series(signal.decimate(do.p.iloc[:,0], 2))
        c = pd.Series(signal.decimate(do.p.iloc[:,1], 2))
        d = pd.Series(signal.decimate(do.p.iloc[:,2], 2))
        e = pd.Series(signal.decimate(do.p.iloc[:,3], 2))
        nt = pd.DataFrame({'0': a,'1':a,'2': a,'3': a})
        nd = pd.DataFrame({'0': b,'1':c,'2': d,'3': e})
        do.t = nt
        do.p = nd  
        do.update_self()

    dsf = do.sr / dsr
        
    a = pd.Series(signal.decimate(do.t.iloc[:,0], int(dsf)))
    b = pd.Series(signal.decimate(do.p.iloc[:,0], int(dsf)))
    c = pd.Series(signal.decimate(do.p.iloc[:,1], int(dsf)))
    d = pd.Series(signal.decimate(do.p.iloc[:,2], int(dsf)))
    e = pd.Series(signal.decimate(do.p.iloc[:,3], int(dsf)))
    nt = pd.DataFrame({'0': a,'1':a,'2': a,'3': a})
    nd = pd.DataFrame({'0': b,'1':c,'2': d,'3': e})
    do.t = nt
    do.p = nd  
    do.update_self()

    return do

def window_helper(do, wl) :
    #def:
    #in:
    #out:

    ns = [[],[],[],[]]
    nt = []

    for i in range(0, len(do.t.iloc[:,0])-wl, wl) :
        ns[0].append(do.p.iloc[i:i+wl,0].mean())
        ns[1].append(do.p.iloc[i:i+wl,1].mean())
        ns[2].append(do.p.iloc[i:i+wl,2].mean())
        ns[3].append(do.p.iloc[i:i+wl,2].mean())
        nt.append(do.t.iloc[i,0])

    do.t = pd.DataFrame({'0': pd.Series(nt),'1':pd.Series(nt),'2': pd.Series(nt),'3': pd.Series(nt)}) 
    do.p = pd.DataFrame({'0': pd.Series(ns[0]),'1':pd.Series(ns[1]),'2': pd.Series(ns[2]),'3': pd.Series(ns[3])}) 

    do.update_self()
        
    return do

def pni_describe(pdf) :
    # def: prints descriptive data to cl for a pni_data_frame
    # in: pdf pni_data_frame (data to describe)
    # out: none
    print("***Sampling Information***")
    print("Mag Identification Number: " +  str(pdf.mn))
    print("Cycle Count: " + str(pdf.cc) + "\nNumber of Oversamples: " + str(pdf.os))
    print("Sampling Rate (Hz): " + str(round(pdf.sr, 3)))
    print('X Component Stdev (nT): ' + str(round(pdf.p.iloc[:, 0].std(), 3)))
    print('Y Component Stdev (nT): ' + str(round(pdf.p.iloc[:, 1].std(), 3)))
    print('Z Component Stdev (nT): ' + str(round(pdf.p.iloc[:, 2].std(), 3)))
    print('|B|-field Stdev (nT): ' + str(round(pdf.p.iloc[:, 3].std(), 3)))
    print("\n") 

def find_best_window(pdf, wl, f, n=1) :
    # def: finds the |B| field lowest stdev for a wl window length in a pni_data_frame
    # in: pdf pni_data_frame (data), wl int window length 
    # out: pdf pni_data_frame containing data from best wl length window

    # window average the data and update lowest stdev
    # note -> assumes that stdev at some point will be less than 1000000
    aod = True if f.find('a') != -1 else False

    mpdf = pdf

    if aod :

        por = []

        for j in range(0, n) :

            istd = 0
            lstd = 1000000
            for i in range(0, (len(mpdf.p.iloc[:,3]) - wl)) :
                s = mpdf.p.iloc[i:i+wl,3].std()
                istd = i if s < lstd else istd
                lstd = s if s < lstd else lstd 
            
            po = quad_data_frame()
            po.c = np.array([pni_data_frame(), pni_data_frame(), pni_data_frame(), pni_data_frame()]) #weird fix for bad python init

            for i in range(0, 4) :
                t = mpdf.c[i].t.iloc[istd:istd+wl, 0]
                x = mpdf.c[i].p.iloc[istd:istd+wl, 0]
                y = mpdf.c[i].p.iloc[istd:istd+wl, 1]
                z = mpdf.c[i].p.iloc[istd:istd+wl, 2]

                b = x.pow(2)+y.pow(2)+z.pow(2) #bpni readings
                b = b.pow(0.5)

                tx = mpdf.c[i].t.iloc[istd:istd+wl,0].to_numpy()[1:]
                ty = mpdf.c[i].t.iloc[istd:istd+wl,0].to_numpy()[:-1]
                tz = tx - ty
                td = pd.Series(tz)

                po.c[i].t = pd.DataFrame({'0': t, '1':t, '2':t, '3':t})
                po.c[i].p = pd.DataFrame({'0': x,'1':y,'2': z,'3': b})
                po.c[i].td = pd.DataFrame({'0': td,'1': td,'2': td,'3': td})
                po.c[i].sr = 1/(td.mean())
                po.c[i].cc = mpdf.c[i].cc
                po.c[i].os = mpdf.c[i].os
                po.c[i].mn = mpdf.c[i].mn
                po.c[i].offset = [0, 0, 0] #just 3 offset values for x,y,z
                po.c[i].calc_offset()

            po.cc = mpdf.cc
            po.os = mpdf.os
            po.mn = mpdf.mn
            po.update_self()

            if n == 1 :
                return po

            for k in range(0,4) :
                x = pd.Series(np.delete(mpdf.c[k].p.iloc[:,0].to_numpy(), slice(istd, istd+wl)))
                y = pd.Series(np.delete(mpdf.c[k].p.iloc[:,1].to_numpy(), slice(istd, istd+wl)))
                z = pd.Series(np.delete(mpdf.c[k].p.iloc[:,2].to_numpy(), slice(istd, istd+wl)))
                t = pd.Series(np.delete(mpdf.c[k].t.iloc[:,0].to_numpy(), slice(istd, istd+wl)))

                mpdf.c[k].t = pd.DataFrame({'0': t, '1':t, '2':t, '3':t})
                mpdf.c[k].p = pd.DataFrame({'0': x,'1':y,'2': z,'3': z})
                
            mpdf.update_self()

            por.append(po)

            print('Found Best Window ' + str(j) + '!\n')

        return por


    else :

        istd = 0
        lstd = 1000000
        for i in range(0, (len(pdf.p.iloc[:,3]) - wl)) :
            s = pdf.p.iloc[i:i+wl,3].std()
            istd = i if s < lstd else istd
            lstd = s if s < lstd else lstd
        
        po = pni_data_frame()

        t = pdf.t.iloc[istd:istd+wl, 0]
        x = pdf.p.iloc[istd:istd+wl, 0]
        y = pdf.p.iloc[istd:istd+wl, 1]
        z = pdf.p.iloc[istd:istd+wl, 2]

        b = x.pow(2)+y.pow(2)+z.pow(2) #bpni readings
        b = b.pow(0.5)

        tx = pdf.t.iloc[istd:istd+wl,0].to_numpy()[1:]
        ty = pdf.t.iloc[istd:istd+wl,0].to_numpy()[:-1]
        tz = tx - ty
        td = pd.Series(tz)

        po.t = pd.DataFrame({'0': t, '1':t, '2':t, '3':t})
        po.p = pd.DataFrame({'0': x,'1':y,'2': z,'3': b})
        po.td = pd.DataFrame({'0': td,'1': td,'2': td,'3': td})
        po.sr = 1/(td.mean())
        po.cc = pdf.cc
        po.os = pdf.os
        po.mn = pdf.mn

        po.offset = [0, 0, 0] #just 3 offset values for x,y,z
        po.calc_offset()

        print('Found Best Window At Index ' + str(istd) + '!\n')

        return po


def fix_corrupted_file(pdf) :
    #
    #
    #

    for i in range(0, len(pdf.iloc[:,0])) :
        if str(pdf.iloc[:,0].iloc[i]) != '4' :
            pdf.drop(labels=i, axis=0, inplace=True)
            print("Found corrupted data at line " + str(i) + '\n' + 'with value')

    return pdf