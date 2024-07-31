from shutil import which
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from scipy.fft import fft, fftfreq, rfft
import pandas as pd
import math
from pickle import TRUE


from . import data_manipulation_lib as dml

center_on_zero = 0 #set to 1 i.e. TRUE if you want the data to be centered around 0
hardset_lim = 0 #set to 1 i.e.e TRUE if you want to hardcode the x and y lims to match the characterization of the PNI

choose_best_window = 1 #set to 1 i.e. TRUE if you want to choose to plot the best x length window for overlayed or downsampled data 
#best_window_length = 48800 #set to number of datapoints you want in your best window -> 39000 is 10 mins at 65 hz
#best_window_length = 39000 #set to number of datapoints you want in your best window -> 39000 is 10 mins at 65 hz
#best_window_length = 1950 #30 seconds at 65 hz
best_window_length = 2340 #30 seconds at 78 hz
#best_window_length = 3900 #60 seconds at 65 hz
#best_window_length = 7800 #90 seconds at 65 hz

plot_colors = ['blue', 'gold', 'tab:red', 'tab:cyan', 'black']

style = 'default'
#style = 'science' #latex version

plt.style.use(style)

params = {
    'font.size': 12,
    'font.family': 'serif',
    'legend.fontsize': 12,
    'xtick.labelsize': 7,
    'ytick.labelsize': 7,
    'xtick.direction': 'in',
    'ytick.direction': 'in',
    'xtick.major.size': 5.0,
    'xtick.minor.size': 3.0,
    'xtick.major.size': 5.0,
    'xtick.minor.size': 3.0,
    'text.usetex': True,
    'figure.figsize': [7.6, 8],
    'axes.xmargin': 0,
    'axes.labelweight' : 'bold',
    'axes.labelsize': 12,
    'xtick.minor.visible' : True,
    'ytick.minor.visible' : True,
}
   
plt.rcParams.update(params)

default_fig_path = 'data_storage/fig/'
default_data_path = 'data_storage/'

def plot_data(f, filename=''):
    # def:
    # in:
    # out:
    gf = True if f.find('f') == -1 else False
    while 1:
        if not gf :
            rf = input("What is the name of the file you want to analyze (processed_data_only)? ")
            iq = input("Is this a quad-mag processed data file (Y/n)?")
            try:
                if iq == 'Y':
                    do = dml.pni_file_decode_quad(default_data_path + rf)
                else :
                    f = f + 'z'
                    do = dml.pni_file_decode_sean(default_data_path + rf, 1, 400, 19)
                break
            except Exception as e:
                print(e)
                print('\nThe file following file could not be found:\n' +  default_data_path + rf + '\n\nTry Again!\n')
        else :
            try:
                do = dml.pni_file_decode_quad(default_data_path + filename)
                break
            except Exception as e:
                print(e)
                print('\nThat file could not be found...hard fault\n')
                return "\nData has not been processed and plotted!"

    sfn = input("What should figures name/number be (avoids overwriting)\n")
    pn = input("\nWhat data do you want to plot? \
        \n1: All Magnetometers Time Series \
        \n2: Single Magnetometer Time Series \
        \n3: IMU \
        \n4: Temperature \
        \n5: All Sensors \
        \n6: Magnetometer PSD \
        \n7: Timestamp \
        \n8: Best Magnetometer Window \
        \n9: Magnetometer Histogram \
        \na: Magnetometer Downsampled Noise \
        \nb: Magnetometer FFT \
        \nEnter Plot Number Here: ")
    dfs = {
        '1': plot_all_magnetometers_time_series,
        '2': plot_single_magnetometer_time_series,
        '3': plot_imu,
        '4': plot_temperature,
        '5': plot_all_sensors,
        '6': plot_magnetometer_psd,
        '7': plot_timestamp,
        '8': plot_best_magnetometer_window,
        '9': plot_magnetometer_hist,
        'a': plot_magnetometer_downsampled_noise,
        'b': plot_magnetometer_fft
    }
    pf = dfs.get(pn, lambda ser: "Failed to plot data!")
    if int(pn, 16) < 1 or int(pn, 16) > 11 :
        print('invalid input')
        plot_data()
    pf(do, sfn, f)
    return "\nData has been processed and plotted"

def plot_all_magnetometers_time_series(do, sfn, f) :
    #def:
    #in:
    #out:

    if f.find('z') != -1 :
        return #do nothing for a non-quad file

    toh = True if input("Do you want to plot all magnetometer readings together (Y/n)? ") == 'Y' else False

    aoh = True if input("Do you want to downsample to 1Hz (Y/n)? ") == 'Y' else False
    
    f = f + 't' if toh else f 

    if choose_best_window and toh :
        do = dml.find_best_window(do, best_window_length, 'a')
    print(do.t)

    if aoh : #downsample to 1hz using scipy decimation feature

        f = f + 'd' #for ylims in plotting

        for i in range(0,4) :
            do.c[i] = dml.decimate_helper(do.c[i], 1)
            dml.pni_describe(do.c[i])

        do.update_self()
        dml.pni_describe(do)
    
    #fix individual mag dataset
    for i in range(0,4) :
        do.c[i].fix_self()
        dml.pni_describe(do.c[i])
    do.update_self()
    dml.pni_describe(do)

    #individual mag figures
    if not toh :
        for i in range(0,4) :
            plot_magnetometer_helper(do.c[i], i, sfn, f + 'a')
    
    #all mags together figure
    plot_magnetometer_helper(do, -1, sfn, f)

def plot_single_magnetometer_time_series(do, sfn, f) :
    #def:
    #in:
    #out:

    z = True if f.find('z') != -1 else False

    if z == False :
        n = input('What magnetometer do you want to plot data for (0 indexed i.e. a number 0-3 should be input, or -1 for quad_mag)? ')
        n = int(n) #cast to an integer for easier use

    aoh = True if input("Do you want to downsample to 1Hz (Y/n)? ") == 'Y' else False

    if aoh : #downsample to 1hz using scipy decimation feature

        if z :
            do = dml.decimate_helper(do, 1)
            dml.pni_describe(do)
        else :    
            if n != -1 :
                do.c[n] = dml.decimate_helper(do.c[n], 1)
                dml.pni_describe(do.c[n])
            else :
                for i in range(0,4) :
                    do.c[i] = dml.decimate_helper(do.c[i], 1)
                dml.pni_describe(do)
    
    #fix individual mag dataset
    if z :
        do.fix_self()
        do.update_self()
        dml.pni_describe(do)
        plot_magnetometer_helper(do, 0, sfn, f + 'a')
    else :        
        if n != -1 :
            do.c[n].fix_self()
            do.c[n].update_self()
            dml.pni_describe(do.c[n])
            plot_magnetometer_helper(do.c[n], n, sfn, f + 'a')
        else :
            #fix individual mag dataset
            for i in range(0,4) :
                do.c[i].fix_self()
            do.update_self()
            dml.pni_describe(do)
            plot_magnetometer_helper(do, n, sfn, f + '')

def plot_magnetometer_helper(do, n, sfn, f) :
    #def:
    #in:
    #out:

    ocns = 3 #num stdev to plot

    a = True if f.find('a') != -1 else False
    h = True if f.find('h') != -1 else False
    t = True if f.find('t') != -1 else False
    d = True if f.find('d') != -1 else False
    q = True if f.find('q') != -1 else False

    if h :
        #HISTOGRAM PLOT
        ic_fig, ic_axs = plt.subplots(3,1)
        labels = ['bx', 'by', 'bz']
        labels_y = ['\\textbf{Count B$_x$}', '\\textbf{Count B$_y$}', '\\textbf{Count B$_z$}']
        titles = ['X-KURT $\Rightarrow$ ', 'Y-KURT $\Rightarrow$ ', 'Z-KURT $\Rightarrow$ ']
        for i in range(0,3) :
            title = titles[i]
            ic_axs[i].set_ylabel(labels_y[i])
            ic_axs[i].set_xlabel('\\textbf{Magnetic Field ($nT$)}')
            py = do.p.iloc[:,i]
            if center_on_zero :
                py = do.p.iloc[:,i] - do.p.iloc[:,i].mean()
            wd = float((1000/(0.3671 * do.cc + 1.5)) / do.os) #/ 4.0 #based on lsb scale factor
            #wd = py.std() #based on standard deviation
            bn = math.ceil((py.max() - py.min()) / wd)
            #bn = 50
            ic_axs[i].hist(py, bins=bn, facecolor='tab:blue', edgecolor='black')
            ic_axs[i].grid(which='both')
            ic_axs[i].grid(which='minor', alpha=0.5, linestyle='--')
            title = title + str(np.round(py.kurtosis(), 3) - 3.000)
            ic_axs[i].set_title(title)
            if hardset_lim :
                ic_axs[i].set_xlim(-25, 25)
            ic_axs[i].ticklabel_format(style='sci', axis='y', scilimits=(0,0))
        ic_fig.tight_layout(pad=1.5)
        #plot single mag
        if a:
            ic_fig.savefig('data_storage/figs/magnetometer_' + str(n) + "_histogram_data_" + str(sfn) + '.png')
        #plot all mags together
        else :
            ic_fig.savefig('data_storage/figs/magnetometer_quad_histogram_data_' + str(sfn) + '.png')
    elif t :
        #TIME SERIES OVERLAYED PLOT
        #NOTE THIS EXPECTS ONLY A QUAD-DATA FRAME AND DOES NOT ADJUST DATA BY DEFAULT
        titles = ['X-STDDEV $\Rightarrow$ ', 'Y-STDDEV $\Rightarrow$ ', 'Z-STDDEV $\Rightarrow$ ']
        ytitles = ['\\textbf{B$_x$ (nT)}', '\\textbf{B$_y$ (nT)}', '\\textbf{B$_z$ (nT)}']
        labels_tex = ['B$_{x_', 'B$_{y_', 'B$_{z_']
        labels_tex_alt = ['$_{B_{x_', '$_{B_{y_', '$_{B_{z_']
        labels = ['bx', 'by', 'bz']
        ic_fig, ic_axs = plt.subplots(3,1)
        for i in range (0,3) : #plot for each axis
            title = titles[i]
            stdsum = 0
            #ic_fig.set_size_inches(18.5, 10.5)
            ic_axs[i].set_ylabel(ytitles[i])
            ic_axs[i].set_xlabel('\\textbf{Time (s)}')
            for j in range (0,4) : #overlay each mag
                px = do.c[j].t.iloc[:,i]
                py = do.c[j].p.iloc[:,i]
                stdsum = stdsum + py.std()
                title = title + str(np.round(py.std(), 3)) + labels_tex_alt[i] + str(j+1) + '}} \\cdot$ '
                if center_on_zero :
                    py = py - py.mean()
                ic_axs[i].plot(px, py, label=labels_tex[i] + str(j+1) + '}$', color=plot_colors[j])
            px = do.t.iloc[:,i]
            py = do.p.iloc[:,i]
            title = title + str(np.round(stdsum/4.0 , 3)) + labels_tex_alt[i] + '{1234}}} \\cdot$ ' + '\\textbf{' + str(np.round(py.std(), 3)) + labels_tex_alt[i] + '{avg}}}$'
            if center_on_zero :
                py = py - py.mean()
            ic_axs[i].plot(px, py, label= '\\textbf{' + labels_tex[i] + '{avg}}$}', color=plot_colors[4], linewidth=3)    
            ic_axs[i].set_title(title)
            ic_axs[i].legend(loc='upper right')
            ic_axs[i].grid(which='both')
            ic_axs[i].grid(which='minor', alpha=0.5, linestyle='--')
            if hardset_lim:
                if d :
                    ic_axs[i].set_ylim(-10,10)
                else :
                    ic_axs[i].set_ylim(-50, 50)

        ic_fig.tight_layout(pad=1.5)
        ic_fig.savefig('data_storage/figs/magnetometer_quad_overlay_' + str(sfn) + '.png', dpi=300)

    elif q :
        #FFT PLOT
        ic_fig, ic_axs = plt.subplots(3,1)
        titles = ['X-Axis', 'Y-Axis', 'Z-Axis']
        labels_y = ['\\textbf{B$_x$ (nT)}', '\\textbf{B$_y$ (nT)}', '\\textbf{B$_z$ (nT)}']
        for i in range(0,3) :
            title = titles[i]
            ic_axs[i].set_ylabel(labels_y[i])
            ic_axs[i].set_xlabel('\\textbf{Frequency ($Hz$)}')
            py = do.p.iloc[:,i]
            if center_on_zero :
                py = do.p.iloc[:,i] - do.p.iloc[:,i].mean()
            num_samples = len(py)
            sample_spacing = 1/do.sr
            yf = fft(np.array(py))
            xf = np.linspace(0.0, 1.0/(2.0*sample_spacing), num_samples//2)
            ic_axs[i].plot(xf, 2.0/num_samples * np.abs(yf[:num_samples//2]), color=plot_colors[i])
            ic_axs[i].grid(which='both')
            ic_axs[i].grid(which='minor', alpha=0.5, linestyle='--')
            ic_axs[i].set_title(title)
            ic_axs[i].ticklabel_format(style='sci', axis='y', scilimits=(0,0))
        ic_fig.tight_layout(pad=1.5)
        #plot single mag
        if a:
            ic_fig.savefig('data_storage/figs/magnetometer_' + str(n) + "_fft_data_" + str(sfn) + '.png')
        #plot all mags together
        else :
            ic_fig.savefig('data_storage/figs/magnetometer_quad_fft_data_' + str(sfn) + '.png')

    else :    
        #TIME SERIES SEPERATE PLOT
        titles = ['X-STDDEV (nT) $\Rightarrow$ ', 'Y-STDDEV (nT) $\Rightarrow$ ', 'Z-STDDEV (nT) $\Rightarrow$ ']
        ytitles = ['\\textbf{B$_x$ (nT)}', '\\textbf{B$_y$ (nT)}', '\\textbf{B$_z$ (nT)}']
        ic_fig, ic_axs = plt.subplots(3,1)
        #ic_axs[3].set_title('b')

        for i in range(0,3) :
            px = do.t.iloc[:,i]
            py = do.p.iloc[:,i]
            if center_on_zero :
                py = do.p.iloc[:,i] - do.p.iloc[:,i].mean()
            ic_axs[i].plot(px, py, color=plot_colors[i])
            #ic_axs[i].plot(px, np.full(len(px), py.mean() - ocns*abs(py.std())), c='black', marker="")
            #ic_axs[i].plot(px, np.full(len(px), py.mean() + ocns*abs(py.std())), c='black', marker="")
            ic_axs[i].set_ylabel(ytitles[i])
            ic_axs[i].set_xlabel('\\textbf{Time (s)}')
            ic_axs[i].set_title(titles[i] + str(np.round(py.std(), 2)))
            #ic_axs[i].legend(loc='lower right')
            ic_axs[i].grid(which='both')
            ic_axs[i].grid(which='minor', alpha=0.5, linestyle='--')
            if hardset_lim :
                if d :
                    ic_axs[i].set_ylim(-10,10)
                else :
                    ic_axs[i].set_ylim(-50, 50)
        ic_fig.tight_layout(pad=1.5)
        #plot single mag
        if a:
            ic_fig.savefig('data_storage/figs/magnetometer_' + str(n) + "_time_series_data_" + str(sfn) + '.png', dpi=300)
        #plot all mags together
        else :
            ic_fig.savefig('data_storage/figs/magnetometer_quad_time_series_data_' + str(sfn) + '.png', dpi=300)

def plot_imu() :
    #def:
    #in:
    #out:
    return 

def plot_temperature() :
    #def:
    #in:
    #out:
    return

def plot_all_sensors() :
    #def:
    #in:
    #out:
    return

def plot_magnetometer_psd(do, sfn, f) :
    #def:
    #in:
    #out:

    n = input('What magnetometer do you want to plot data for (0 indexed i.e. a number 0-3 should be input, or -1 for quad_mag)? ')

    n = int(n) #cast to an integer for easier use

    aoh = True if input("Do you want to downsample to 1Hz (Y/n)? ") == 'Y' else False

    wlaon = 5 if (n == -1 and choose_best_window) else 1

    if wlaon == 1 :
        do = [do]

    if choose_best_window :
        if n != -1:
            do.c[n] = dml.find_best_window(do, best_window_length, '')
        else :
            do = dml.find_best_window(do, best_window_length, 'a', wlaon)

    if aoh : #downsample to 1hz using scipy decimation feature

        if n != -1 :
            do.c[n] = dml.decimate_helper(do.c[n], 1)
            dml.pni_describe(do.c[n])
        else :
            for j in range(0, wlaon) :
                for i in range(0,4) :
                    do[j].c[i] = dml.decimate_helper(do[j].c[i], 1)
                dml.pni_describe(do[j])

    #fix individual mag dataset
    if n != -1 :
        do.c[n].fix_self()
        do.c[n].update_self()
        dml.pni_describe(do.c[n])
    else :
        #fix individual mag dataset
        for j in range (0,wlaon) :
            for i in range(0,4) :
                do[j].c[i].fix_self()
            do[j].update_self()
            dml.pni_describe(do[j])

    labels_tex = ['B$_{x_{', 'B$_{y_{', 'B$_{z_{', '\\textbf{B}']
    labels_tex_alt = ['$_{B_{x_', '$_{B_{y_', '$_{B_{z_']
    labels = ['bx', 'by', 'bz']
    titles = ['NOISE DENSITY @ 1 $Hz$ $\Rightarrow$ ', 'NOISE DENSITY @ 1 $Hz$ $\Rightarrow$ ', 'NOISE DENSITY @ 1 $Hz$ $\Rightarrow$ ']
    labels_y = ['\\textbf{Noise Density B$_x$ $(\\frac{nT}{\\sqrt{Hz}}$)}', '\\textbf{Noise Density B$_y$ $(\\frac{nT}{\\sqrt{Hz}}$)}', '\\textbf{Noise Density B$_z$ $(\\frac{nT}{\\sqrt{Hz}}$)}']
    ic_fig, ic_axs = plt.subplots(3,1)
    for j in range(0,3) :
        title = titles[j]
        ic_axs[j].set_ylabel(labels_y[j])
        #ic_axs[j].set_ylabel('\\textbf{Power Spectrum ($nT$ RMS)}')
        ic_axs[j].set_xlabel('\\textbf{Frequency ($Hz$)}')
        ohr = 0
        for i in range (0,wlaon) : #plot for each axis
            #title = titles[i]
            #stdsum = 0
            py = do[i].p.iloc[:, j]
            srd = do[i].sr
            if n != -1 :
                py = do[i].c[n].p.iloc[:,j]
                srd = do[i].c[n].sr
            #title = title + str(np.round(stdsum/4.0 , 3)) + labels_tex_alt[i] + '{1234}}} \\cdot$ ' + '\\textbf{' + str(np.round(py.std(), 3)) + labels_tex_alt[i] + '{avg}}}$'
            if center_on_zero :
                py = py - py.mean()
                
            #ic_axs[j].psd(py, Fs=int(srd), color=plot_colors[4], linewidth=3)    
            #fx, psdx = signal.welch(py, int(srd), 'flattop', 1024, scaling='spectrum')
            fx, psdx = signal.welch(py, srd, 'hamming', nperseg=len(py)/2)
            psdx = np.sqrt(psdx)

            for l,m in enumerate(fx) :
                if m > 1 :
                    ohr = ohr + psdx[l]
                    break

            #print(np.mean(psdx[int(len(psdx)/2):]))
            #ic_axs[j].semilogy(fx, psdx, label=labels_tex[j] + str(i) + '}}$', color=plot_colors[i])
            ic_axs[j].loglog(fx, psdx)


        ohr = ohr / float(wlaon)

        ic_axs[j].set_title(title + str(np.round(ohr, 3)) + ' $nT$/$\\sqrt{Hz}$')
        #ic_axs[j].legend(loc='upper right')
        ic_axs[j].grid(which='both')
        ic_axs[j].grid(which='minor', alpha=0.5, linestyle='--')
        if hardset_lim :
            ic_axs[j].set_ylim(.1, 10)
            #ic_axs[j].set_xlim(0, 10)   
    
    ic_fig.tight_layout(pad=2)

    if n != -1:
        ic_fig.savefig('data_storage/figs/magnetometer_' + str(n) + '_psd_' + str(sfn) + '.png', dpi=300)
    #plot all mags together
    else :
        ic_fig.savefig('data_storage/figs/magnetometer_quad_psd_' + str(sfn) + '.png', dpi=300)

    return

def plot_timestamp() :
    #def:
    #in:
    #out:
    return

def plot_best_magnetometer_window(do, sfn, f) :
    #def: plots the best window of data for a single or all magnetometers, time series
    #in: 
    #out:
    
    n = input('What magnetometer do you want to find the best window for (0 indexed i.e. a number 0-3 should be input, or -1 for quad_mag)? ')

    wl = input('How many data points do you want in your window? ')

    n = int(n) #cast to an integer for easier use

    wl = int(wl) #cast to an integer for easier use

    aoh = True if input("Do you want to downsample to 1Hz (Y/n)? ") == 'Y' else False

    if aoh : #downsample to 1hz using scipy decimation feature

        if n != -1 :
            do.c[n] = dml.decimate_helper(do.c[n], 1)
        else :
            for i in range(0,4) :
                do.c[i] = dml.decimate_helper(do.c[i], 1)
            do.update_self()

    don = dml.find_best_window(do.c[n], wl, '') if n != -1 else dml.find_best_window(do, wl, 'a')

    dml.pni_describe(don)

    f = f + 'a' if n != -1 else ''

    plot_magnetometer_helper(don, n, sfn, f)

def plot_magnetometer_hist(do, sfn, f) :

    n = input('What magnetometer do you want to plot the histogram for (0 indexed i.e. a number 0-3 should be input, or -1 for quad_mag)? ')

    n = int(n) #cast to an integer for easier use

    aoh = True if input("Do you want to downsample to 1Hz (Y/n)? ") == 'Y' else False

    if aoh : #downsample to 1hz using scipy decimation feature

        if n != -1 :
            do.c[n] = dml.decimate_helper(do.c[n], 1)
        else :
            for i in range(0,4) :
                do.c[i] = dml.decimate_helper(do.c[i], 1)
            do.update_self()

    f = f + 'ah' if n != -1 else 'h'

    if n != -1 :
        do.c[n].fix_self()
        do.c[n].update_self()
        dml.pni_describe(do.c[n])
        plot_magnetometer_helper(do.c[n], n, sfn, f)
    else :
        #fix individual mag dataset
        for i in range(0,4) :
            do.c[i].fix_self()
        do.update_self()
        dml.pni_describe(do)
        plot_magnetometer_helper(do, n, sfn, f)


def plot_magnetometer_downsampled_noise(do, sfn, f) :

    if choose_best_window :
        do = dml.find_best_window(do, best_window_length, 'a')

    #create array of sample rates
    srx = [float(np.floor(do.sr))]
    tsr = float(np.floor(do.sr))
    while((tsr/2.0) > 0.1) :
        srx.append(tsr/2.0)
        tsr = tsr / 2.0
    srx.append(0.1)
    x2d = [[],[],[],[],[]]
    y2d = [[],[],[],[],[]]
    z2d = [[],[],[],[],[]]
    for i,j in enumerate(srx) :
        tdo = do
        for k in range(0,4) :
            ndo = dml.decimate_helper(tdo.c[k], j)
            x2d[k].append(ndo.p.iloc[:,0].std())
            y2d[k].append(ndo.p.iloc[:,1].std())
            z2d[k].append(ndo.p.iloc[:,2].std())
        tdo.update_self()
        x2d[4].append(tdo.p.iloc[:,0].std())
        y2d[4].append(tdo.p.iloc[:,1].std())
        z2d[4].append(tdo.p.iloc[:,2].std())

    titles = ['STDDEV @ 0.1 $Hz$ $\Rightarrow$ ', 'STDDEV @ 0.1 $Hz$ $\Rightarrow$ ', 'STDDEV @ 0.1 $Hz$ $\Rightarrow$ ']
    ytitles = ['\\textbf{Noise Level B$_x$ (nT)}', '\\textbf{Noise Level B$_y$ (nT)}', '\\textbf{Noise Level B$_z$ (nT)}']
    labels_tex = ['B$_{x_', 'B$_{y_', 'B$_{z_']
    labels = ['bx', 'by', 'bz']
    xyz3d = [x2d, y2d, z2d]
    ic_fig, ic_axs = plt.subplots(3,1)
    for i in range (0,3) : #plot for each axis
        title = titles[i]
        ic_axs[i].set_title(title + str(np.round(xyz3d[i][4][-1], 3)) + ' $nT$')
        #stdsum = 0
        ic_axs[i].set_ylabel(ytitles[i])
        ic_axs[i].set_xlabel('\\textbf{Sampling Rate (Hz)}')
        for j in range (0,4) : #overlay each mag
            px = srx
            py = xyz3d[i][j]
            #stdsum = stdsum + py.std()
            #title = title + str(np.round(py.std(), 3)) + ', '
            ic_axs[i].semilogx(px, py, label=labels_tex[i] + str(j+1) + '}$', color=plot_colors[j], marker='x', markersize=4, markeredgewidth=2)
        px = srx
        py = xyz3d[i][4]
        #title = title + str(np.round(stdsum/4.0 , 3)) + ', ' + str(np.round(py.std(), 3))
        ic_axs[i].semilogx(px, py, label=labels_tex[i] + '{avg}}$', color=plot_colors[4], marker='x', markersize=4, markeredgewidth=2, linewidth=2)    
        #ic_axs[i].set_title(title)
        ic_axs[i].legend(loc='upper right')
        ic_axs[i].grid(which='both')
        ic_axs[i].grid(which='minor', alpha=0.5, linestyle='--')
        if hardset_lim :
            ic_axs[i].set_ylim(0, 15)

    ic_fig.tight_layout(pad=1.5)
    ic_fig.savefig('data_storage/figs/magnetometer_quad_downsampled_noise_' + str(sfn) + '.png', dpi=300)

def plot_magnetometer_fft(do, sfn, f) :
    
    z = True if f.find('z') != -1 else False

    if z == False :
        n = input('What magnetometer do you want to plot data for (0 indexed i.e. a number 0-3 should be input, or -1 for quad_mag)? ')
        n = int(n) #cast to an integer for easier use

    aoh = True if input("Do you want to downsample to 1Hz (Y/n)? ") == 'Y' else False

    if aoh : #downsample to 1hz using scipy decimation feature

        if z :
            do = dml.decimate_helper(do, 1)
            dml.pni_describe(do)
        else :    
            if n != -1 :
                do.c[n] = dml.decimate_helper(do.c[n], 1)
                dml.pni_describe(do.c[n])
            else :
                for i in range(0,4) :
                    do.c[i] = dml.decimate_helper(do.c[i], 1)
                dml.pni_describe(do)
    
    #fix individual mag dataset
    if z :
        do.fix_self()
        do.update_self()
        dml.pni_describe(do)
        plot_magnetometer_helper(do, 0, sfn, f + 'qa')
    else :        
        if n != -1 :
            do.c[n].fix_self()
            do.c[n].update_self()
            dml.pni_describe(do.c[n])
            plot_magnetometer_helper(do.c[n], n, sfn, f + 'qa')
        else :
            #fix individual mag dataset
            for i in range(0,4) :
                do.c[i].fix_self()
            do.update_self()
            dml.pni_describe(do)
            plot_magnetometer_helper(do, n, sfn, f + 'q')
