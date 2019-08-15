'''
This program is a rudimentary music transcriber. It uses fast Fourier transform to extract the frequency
spectrum from a moving time window. The Harmonic Sum Spectrum is used to identify pitches and generate
a chromagram. A second derivative peak detection algorithm is used to detect note onset and duration.
Note starts and end times are aligned based on overlapping and adjacent notes. Note duration is then assigned
to the closest matching assignable note duration. The inaccuracies in the results illustrate challenges in
music transcription such as octave errors, interference from harmonics, note decay overlap, and beat detection.
'''

import numpy as np
from scipy.io import wavfile
import matplotlib.pyplot as plt
from sklearn import linear_model
from sklearn.metrics import r2_score
import abjad as ab
from tkinter import *
from tkinter.ttk import *

# Graphic User Interface for Parameter Settings

loopactive=True
window = Tk(className=' Settings')
frame = Frame(window,width=1200, height=800)
frame.pack(fill=BOTH, expand=True )

filelabel = Label(frame,text='File Path and Name')
fileentry = Entry(frame,width=80)

headinglabel1 = Label(frame,text='PITCH RECOGNITION')

intervallabel = Label(frame,text='Moving FFT Window Size (ms)')
intervalentry = Entry(frame,width=5)
intervalentry.insert(0,300)

steplabel = Label(frame,text='Moving FFT Step Size (ms)')
stepentry = Entry(frame,width=5)
stepentry.insert(0,10)

upfreqlabel = Label(frame,text='Upper Frequency (Hz)')
upfreqentry = Entry(frame,width=5)
upfreqentry.insert(0,8000)

lowfreqlabel = Label(frame,text='Lower Frequency (Hz)')
lowfreqentry = Entry(frame,width=5)
lowfreqentry.insert(0,20)

maxharmlabel = Label(frame,text='Maximum Number of Harmonics')
maxharmentry = Entry(frame,width=5)
maxharmentry.insert(0,20)

thresholdlabel = Label(frame,text='HSS Threshold (Fraction of Maximum FFT Coefficient for Exclusion)')
thresholdentry = Entry(frame,width=5)
thresholdentry.insert(0,0.04)

minthresholdlabel = Label(frame,text='Minimum Absolute HSS Threshold')
minthresholdentry = Entry(frame,width=8)
minthresholdentry.insert(0,50000)

detectionlabel = Label(frame,text='Minimum Absolute Threshold for Undertone Subtraction')
detectionentry = Entry(frame,width=8)
detectionentry.insert(0,50000)

adjustmentlabel = Label(frame,text='Tuning Adjustment (Half-Tones)')
adjustmententry = Entry(frame,width=5)
adjustmententry.insert(0,0.1)

headinglabel2 = Label(frame,text='TRANSCRIPTION REGION')

analysisstartlabel = Label(frame,text='Start Transcription (points)')
analysisstartentry = Entry(frame,width=5)
analysisstartentry.insert(0,0)

analysisstoplabel = Label(frame,text='End Transcription (points)')
analysisstopentry = Entry(frame,width=5)
analysisstopentry.insert(0,1000)

analysissteplabel = Label(frame,text='Transcription Step Size (points)')
analysisstepentry = Entry(frame,width=5)
analysisstepentry.insert(0,1)

headinglabel3 = Label(frame,text='NOTE DETECTION')

onsetthresholdlabel = Label(frame,text='Note Onset Absolute Threshold')
onsetthresholdentry = Entry(frame,width=5)
onsetthresholdentry.insert(0,1000000)

onsetfractionlabel = Label(frame,text='Note Onset Relative Threshold (Fraction of Maximum)')
onsetfractionentry = Entry(frame,width=5)
onsetfractionentry.insert(0,0.5)

extremawindow1label = Label(frame,text='Extrema Detection Window (transcription steps)')
extremawindow1entry = Entry(frame,width=5)
extremawindow1entry.insert(0,10)

firstderivwindowlabel = Label(frame,text='First Derivative Window (transcription steps)')
firstderivwindowentry = Entry(frame,width=5)
firstderivwindowentry.insert(0,10)

secondderivwindowlabel = Label(frame,text='Second Derivative Window (transcription steps)')
secondderivwindowentry = Entry(frame,width=5)
secondderivwindowentry.insert(0,10)

extremawindow2label = Label(frame,text='Derivative Extrema Detection Window (transcription steps)')
extremawindow2entry = Entry(frame,width=5)
extremawindow2entry.insert(0,10)

maxmatchwindowlabel = Label(frame,text='Signal & Second Derivative Match Window (transcription steps)')
maxmatchwindowentry = Entry(frame,width=5)
maxmatchwindowentry.insert(0,15)

headinglabel4 = Label(frame,text='RHYTHM ALIGNMENT')

shortthresholdlabel = Label(frame,text='Threshold for Short Note Exclusion (transcription steps)')
shortthresholdentry = Entry(frame,width=5)
shortthresholdentry.insert(0,5)

alignthresholdlabel = Label(frame,text='Discrepancy Threshold for Track Alignment (transcription steps)')
alignthresholdentry = Entry(frame,width=5)
alignthresholdentry.insert(0,5)

alignendsthresholdlabel = Label(frame,text='Threshold for Note End-Note Start Alignment (transcription steps)')
alignendsthresholdentry = Entry(frame,width=5)
alignendsthresholdentry.insert(0,10)

durationbiaslabel = Label(frame,text='Even Note Duration Bias (32nd note)')
durationbiasentry = Entry(frame,width=5)
durationbiasentry.insert(0,0.25)

subdivisionslabel = Label(frame,text='Subdivisions for Tempo Determination')
subdivisionsentry = Entry(frame,width=5)
subdivisionsentry.insert(0,1)

evaluationwindowlabel = Label(frame,text='Tempo Window for Evaluation (40/FFT step)')
evaluationwindowentry = Entry(frame,width=5)
evaluationwindowentry.insert(0,10)

restadjustmentgainlabel = Label(frame,text='Threshold Improvement for Length Adjustment')
restadjustmentgainentry = Entry(frame,width=5)
restadjustmentgainentry.insert(0,5)

adjustmentwindowlabel = Label(frame,text='Allowable Window for Length Adjustment')
adjustmentwindowentry = Entry(frame,width=5)
adjustmentwindowentry.insert(0,10)

headinglabel5 = Label(frame,text='OUTPUT FORMAT')

analysisstaveslabel = Label(frame,text='Output Staves')
stavesanalyzed= StringVar()
analysisstavescombo = Combobox(frame, textvariable=stavesanalyzed)
analysisstavescombo['values']=['Treble','Bass','Treble+Bass']
stavesanalyzed.set('Treble+Bass')

# OK button escapes loop

def done():
    global loopactive
    window.update_idletasks()
    window.withdraw()
    loopactive = False
okbutton =Button(frame, text='OK', command=done)

filelabel.grid(row=0, column = 0, sticky=E)
fileentry.grid(row=0, column = 1, sticky=W)

headinglabel1.grid(row=1, column = 0, sticky=E)

intervallabel.grid(row=2, column = 0, sticky=E)
intervalentry.grid(row=2, column = 1, sticky=W)
steplabel.grid(row=3, column = 0, sticky=E)
stepentry.grid(row=3, column = 1, sticky=W)
upfreqlabel.grid(row=4, column = 0, sticky=E)
upfreqentry.grid(row=4, column = 1, sticky=W)
lowfreqlabel.grid(row=5, column = 0, sticky=E)
lowfreqentry.grid(row=5, column = 1, sticky=W)
maxharmlabel.grid(row=6, column = 0, sticky=E)
maxharmentry.grid(row=6, column = 1, sticky=W)
thresholdlabel.grid(row=7, column = 0, sticky=E)
thresholdentry.grid(row=7, column = 1, sticky=W)
minthresholdlabel.grid(row=8, column = 0, sticky=E)
minthresholdentry.grid(row=8, column = 1, sticky=W)
detectionlabel.grid(row=9, column = 0, sticky=E)
detectionentry.grid(row=9, column = 1, sticky=W)
adjustmentlabel.grid(row=10, column = 0, sticky=E)
adjustmententry.grid(row=10, column = 1, sticky=W)

headinglabel2.grid(row=11, column = 0, sticky=E)

analysisstartlabel.grid(row=12, column = 0, sticky=E)
analysisstartentry.grid(row=12, column = 1, sticky=W)
analysisstoplabel.grid(row=13, column = 0, sticky=E)
analysisstopentry.grid(row=13, column = 1, sticky=W)
analysissteplabel.grid(row=14, column = 0, sticky=E)
analysisstepentry.grid(row=14, column = 1, sticky=W)

headinglabel3.grid(row=15, column = 0, sticky=E)

onsetthresholdlabel.grid(row=16, column = 0, sticky=E)
onsetthresholdentry.grid(row=16, column = 1, sticky=W)
onsetfractionlabel.grid(row=17, column = 0, sticky=E)
onsetfractionentry.grid(row=17, column = 1, sticky=W)
extremawindow1label.grid(row=18, column = 0, sticky=E)
extremawindow1entry.grid(row=18, column = 1, sticky=W)
firstderivwindowlabel.grid(row=19, column = 0, sticky=E)
firstderivwindowentry.grid(row=19, column = 1, sticky=W)
secondderivwindowlabel.grid(row=20, column = 0, sticky=E)
secondderivwindowentry.grid(row=20, column = 1, sticky=W)
extremawindow2label.grid(row=21, column = 0, sticky=E)
extremawindow2entry.grid(row=21, column = 1, sticky=W)
maxmatchwindowlabel.grid(row=22, column = 0, sticky=E)
maxmatchwindowentry.grid(row=22, column = 1, sticky=W)

headinglabel4.grid(row=23, column = 0, sticky=E)

shortthresholdlabel.grid(row=24, column = 0, sticky=E)
shortthresholdentry.grid(row=24, column = 1, sticky=W)
alignthresholdlabel.grid(row=25, column = 0, sticky=E)
alignthresholdentry.grid(row=25, column = 1, sticky=W)
alignendsthresholdlabel.grid(row=26, column = 0, sticky=E)
alignendsthresholdentry.grid(row=26, column = 1, sticky=W)
durationbiaslabel.grid(row=27, column = 0, sticky=E)
durationbiasentry.grid(row=27, column = 1, sticky=W)
subdivisionslabel.grid(row=28, column = 0, sticky=E)
subdivisionsentry.grid(row=28, column = 1, sticky=W)
evaluationwindowlabel.grid(row=29, column = 0, sticky=E)
evaluationwindowentry.grid(row=29, column = 1, sticky=W)
restadjustmentgainlabel.grid(row=30, column = 0, sticky=E)
restadjustmentgainentry.grid(row=30, column = 1, sticky=W)
adjustmentwindowlabel.grid(row=31, column = 0, sticky=E)
adjustmentwindowentry.grid(row=31, column = 1, sticky=W)

headinglabel5.grid(row=32, column = 0, sticky=E)

analysisstaveslabel.grid(row=33, column = 0, sticky=E)
analysisstavescombo.grid(row=33, column = 1, sticky=W)

okbutton.grid(row=34, column = 1, sticky = W)

while loopactive:
    window.update()

# PARAMETER SETTING

# Import specified .wav file
file =fileentry.get()

# Define moving window parameters
interval = int(intervalentry.get()) # Time interval for fft in ms
step = int(stepentry.get()) # Step size in ms
upperfreq = int(upfreqentry.get())
lowerfreq = int(lowfreqentry.get())
maxharm = int(maxharmentry.get())
threshold = float(thresholdentry.get())
minthreshold = int(minthresholdentry.get())
detection = int(detectionentry.get())
adjustment = float(adjustmententry.get()) # Adjustment for out of tune instrument or alternative tuning

# Analysis Region
analysisstart = int(analysisstartentry.get())
analysisstop = int(analysisstopentry.get())
analysisstep = int(analysisstepentry.get())

# Note Detection Parameters
onsetthreshold = int(onsetthresholdentry.get())
onsetfraction =float(onsetfractionentry.get())
extremawindow1 = int(extremawindow1entry.get())
firstderivwindow = int(firstderivwindowentry.get())
secondderivwindow = int(secondderivwindowentry.get())
extremawindow2 = int(extremawindow2entry.get())
maxmatchwindow = int(maxmatchwindowentry.get())

# Rhythm Alignment Parameters
shortthreshold = int(shortthresholdentry.get())
alignthreshold = int(alignthresholdentry.get())
alignendsthreshold = int(alignendsthresholdentry.get())
durationbias = float(durationbiasentry.get())
subdivisions = int(subdivisionsentry.get())
evaluationwindow = int(evaluationwindowentry.get())
restadjustmentgain = int(restadjustmentgainentry.get())
adjustmentwindow = int(adjustmentwindowentry.get())
analysisstaves = stavesanalyzed.get()

window.destroy()

# Read Audio File
rate, audio = wavfile.read(file)

# Calculation of Other Basic Parameters
intervalpts = int(interval*rate/1000) # Time interval in data points
steppts = int(step*rate/1000) # Step in data points
numfreq = int((upperfreq/rate)*intervalpts)

# Average stereo channels
if audio.shape[1]>1:
    audio = np.mean(audio,axis=1)

# Frequency axis points
freq = (np.arange(int(intervalpts/2))/interval*1000)[:numfreq]

# Fast Fourier Transform function
def amplitudes(steps):
    segment = audio[steps*steppts:steps*steppts+intervalpts:1]
    return abs(np.fft.rfft(segment))[:int(intervalpts/2)][:numfreq]

# Harmonic Product Spectrum(input result of fft)
def hps(spectrum):
    hpspectrum = (spectrum[:]-max(minthreshold,threshold*max(spectrum)))/max(spectrum) # Filter and normalize
    hpspectrum+=1 # To ensure no signals are decreased during multiplication
    for i in range(0,numfreq):
        if hpspectrum[i] <= 1: # So signals below threshold have no effect
            hpspectrum[i]=1
    for i in range(1+int((lowerfreq/rate)*intervalpts),numfreq//2):
        if hpspectrum[i] > 1:
            for j in range(1, min(maxharm, numfreq // i)): # Product of harmonic signals
                hpspectrum[i] *= hpspectrum[i * j]
    hpspectrum -=1
    if max(hpspectrum)!=0: # Rescale
        hpspectrum = hpspectrum*max(spectrum)/max(hpspectrum)
    return hpspectrum

# Harmonic Sum Spectrum(input result of fft)
def hss(spectrum):
    hsspectrum = (spectrum[:]-max(minthreshold,threshold*max(spectrum)))/max(spectrum) # Filter and normalize
    for i in range(0,numfreq):
        if hsspectrum[i] <= 0: # So signals below threshold have no effect
            hsspectrum[i]=0
    for i in range(1+int((lowerfreq/rate)*intervalpts),numfreq//2):
        if hsspectrum[i] > 0:
            for j in range(1, min(maxharm, numfreq // i)): # Sum of harmonic signals
                hsspectrum[i] += hsspectrum[i * j]
    if max(hsspectrum)!=0: # Rescale
        hsspectrum = hsspectrum*max(spectrum)/max(hsspectrum)
    return hsspectrum

# Detection Spectrum (input result of fft)
def fhss(spectrum): # Assumes a note is made up of a uniform distribution of harmonics
    harmsum = hss(spectrum)
    dspec = np.zeros(numfreq) # Difference spectrum (subtracting contributions from harmonics of lower notes)
    for i in range(3,numfreq): # Ignore lowest frequencies
        harmonics = 1/np.arange(2,min(i,maxharm)) # Harmonic series
        undertones = np.zeros(len(harmonics))
        for j in range(0,min(i,maxharm)-2):
            undertones[j]=harmsum[int(round(i*harmonics[j]))] # Returns lower note harmonics interfering with note
        hthreshold = np.dot(harmonics,undertones) # Theoretical contribution to signal from harmonics of lower notes
        if harmsum[i]>=detection and harmsum[i]>= hthreshold:
            dspec[i]=(harmsum[i]-hthreshold)/harmsum[i]
    return dspec*harmsum

# Conversion of frequency to linear pitch space
def pitch(x):
    if x == 0:
        return -88
    else:
        return int(round(69 + adjustment + 12 * np.log2(x / 440))) # MIDI note numbering scale

vpitch= np.vectorize(pitch) # Vectorize conversion function
tone = vpitch(freq) # Conversion of frequency axis to pitch
tones = np.arange(-88,1+int(round(69 + 12 * np.log2(upperfreq / 440))))

# Function that bins and sums values according to pitch
def amplitude(steps):
    amp = np.zeros(89+int(round(69 + 12 * np.log2(upperfreq / 440))))
    x = fhss(amplitudes(steps))
    for i in range(0, len(tone)):
        amp[tone[i]+88] += x[i]
    return amp

# Moving Average
def movingavg(x, n):
    a = np.cumsum(x,axis=1)
    return (a-np.concatenate((np.zeros((len(a),n)),a[:,:-n]),axis=1))/n

# First Derivative
def deriv(x,n):
    rshiftx = np.concatenate((np.zeros((len(x),n)),x[:,:-n]),axis=1)
    lshiftx = np.concatenate((x[:,n:],np.zeros((len(x), n))), axis=1)
    return lshiftx-rshiftx

# Second Derivative
def deriv2(x,n,m):
    return deriv(deriv(x,n),m)

# Extrema detection
def extrema(x,n):
    a = np.zeros_like(x)
    for i in range(0,x.shape[0]):
        for j in range(n,x.shape[1]-n):
            counter = 0
            for k in range(1,n+1):
                if x[i,j]>= x[i,j-k] and x[i,j]>=x[i,j+k]: # For maxima
                    counter +=1
                elif x[i,j]<= x[i,j-k] and x[i,j]<=x[i,j+k]: # For minima
                    counter -=1
            if counter == n:
                a[i,j]=1
            elif counter == -1*n:
                a[i,j]=-1
    return a

# Threshold activation (0 if below threshold, 1 if above), to be used on chromagram
def thresh(x,limit,fraction):
    a = np.zeros_like(x)
    maxarray = x.max(axis=0)
    meanarray = np.mean(x,axis=0)
    for i in range(0, x.shape[0]):
        for j in range(0, x.shape[1]):
            if x[i,j] >= limit and (x[i,j]/maxarray[j]>=fraction or x[i,j]/meanarray[j]>=25):
                a[i,j] = 1
    return a

# Boundary, to be used on threshold activation array of chromagram
def boundary(x):
    a = np.zeros_like(x)
    for i in range(0, x.shape[0]):
        for j in range(1, x.shape[1]-1):
            if x[i,j]>0 and x[i,j-1]<=0: # For start
                a[i,j]=1
            elif x[i,j]>0 and x[i,j+1]<=0: # For end
                a[i,j]=-1
    return a

# Match Maxima (x should be d2/dt2 and y should be chromagram extrema array)
def matchmax(x,y,n):
    a = np.zeros_like(x)
    for i in range(0,x.shape[0]):
        for j in range(n,x.shape[1]-n):
            for k in range(0,n+1):
                if y[i,j-k]>0 or y[i,j+k]>0:
                    a[i,j]=1
    return a*x

# Chromagram generation
time = []
chromagramT = []

def chromagraph(start,stop,step): # Generates chromagram
    global time
    global chromogramT
    for i in range(start, stop//step):
        time.append(i * step) # Create list of time values
        x = amplitude(i * step) # Create list of signal values
        chromagramT.append(x)
    chromagram = np.array(chromagramT)
    chromagram = np.transpose(chromagram)
    chromagram = movingavg(chromagram, 40//step) # Smooth via moving average
    time = np.array(time)
    return chromagram

# Function marks the start and end of each note in each tone channel
def findnotes(x): # To be used on a chromagram
    t = thresh(x,onsetthreshold,onsetfraction) # Array entry is 1 if within a note (signal above threshold) and 0 if not
    bounds = boundary(t) # Entry is 1 if at the beginning of the note, -1 if at end, 0 otherwise
    exx = extrema(x,extremawindow1)
    d2x = -1*deriv2(x,firstderivwindow,secondderivwindow) # d2x/dt2 of chromagram
    exd2x = extrema(d2x,extremawindow2) # 1 if d2x/dt2 maximum, -1 if d2x/dt2 minimum
    m = matchmax(exd2x,exx,maxmatchwindow) # 1 if d2x/dt2 maximum matches x(t) maximum
    a = np.zeros_like(x) # Array indicating note start and stop
    for i in range(0, x.shape[0]):
        tracker = 0
        lastend = 0
        firststart = 0
        for j in range(1, x.shape[1] - 1):
            if t[i, j] == 1 and exd2x[i, j] == 1:
                tracker += 1 # Within a note, each d2x/dt2 maximum is counted
                lastend = j
            elif t[i, j] == 0:
                if bounds[i,j-1]==-1: # If at the end of a note
                    if m[i,lastend] == 0 and lastend !=firststart: # If the last d2x/dt2 maximum is not an x(t) maximum
                        a[i,lastend]=-1 # It is set as the note end
                    elif tracker != 0:
                        a[i,j-1]=-1 # Otherwise the note end is set once signal falls below threshold
                lastend = 0
                firststart = 0
                tracker = 0  # Resets to 0 when signal falls below threshold
            if tracker == 1 and exd2x[i, j] == 1: # For first d2x/dt2 maximum in a note
                a[i, j] = 1 # Code for start of a note
                firststart = j
            elif tracker > 1 and m[i, j] > 0: # For subsequent d2x/dt2 maxima that are also x(t) maxima
                a[i, j-1] = -1
                a[i, j] = 1
    return a

# Function creates array of all note starts
def starts(x): # To be used on findnotes() output
    xstarts = np.zeros(x.shape[1])
    for i in range(0, x.shape[1]):
        for j in range(0, x.shape[0]):
            if x[j, i] == 1:
                xstarts[i] = 1
    return xstarts

# Function creates array of all note ends
def ends(x): # To be used on findnotes() output
    xends = np.zeros(x.shape[1])
    for i in range(0, x.shape[1]):
        for j in range(0, x.shape[0]):
            if x[j, i] == -1:
                xends[i] = -1
    return xends

# Function removes notes shorter than threshold value
def removeshort(x,n):
    for i in range(0,x.shape[0]):
        tracker = 0
        laststart= 0
        for j in range(0, x.shape[1]):
            if x[i,j] == 1:
                laststart = j
                tracker = 0
            elif x[i,j] == 0:
                tracker +=1
            elif x[i,j] ==-1:
                laststop = j
                if tracker < n:
                    x[i,laststart]=0
                    x[i,laststop]=0
                tracker = 0
    return x

# Function aligns note start from different channels (perform before splitting staves)
def alignstart(x,n): # Modifies findnotes() output
    xstarts = starts(x)
    zerocount = 0
    clusterlist = []
    for i in range(0,len(xstarts)):
        if xstarts[i]==0:
            zerocount +=1
        else:
            zerocount = 0
            clusterlist.append(i)
        if zerocount > n:
            if clusterlist:
                avg = int(round(sum(clusterlist) / len(clusterlist)))
                for i in clusterlist:
                    for j in range(0, x.shape[0]):
                        if x[j,i]==1:
                            x[j,i]=0
                            x[j, avg] = 1
                clusterlist = []
    return x

# Function aligns note ends with beginning of next note (perform before and after splitting staves)
def alignends(x,n): # Modifies findnotes() output
    xstarts = starts(x)
    for i in range(0,x.shape[0]):
        spacecount = 0
        startcount = False
        note = False
        lastend = None
        for j in range(0,x.shape[1]):
            if xstarts[j]==1 and note: # Aligns note end with next note start
                note = False
                startcount = False
                if spacecount < n and j>0: # Aligns only if space is below a threshold n
                    if lastend and lastend !=j-1:
                        x[i, j - 1] = -1
                        x[i, lastend] = 0
                    elif not lastend:
                        x[i, j - 1] = -1
                spacecount = 0
                lastend = None
            if x[i,j]==1:
                note = True
            if x[i,j]==-1:
                if not note:
                    x[i,j]=0
                else:
                    startcount=True
                    lastend = j
            if startcount and note and xstarts[j]==0:
                spacecount +=1
    endcount = 0
    endlist = []
    xends = ends(x)
    for i in range(0, x.shape[1]): # Aligns ends of different notes to the same time
        if xstarts[i] == 1:
            if xends[i] == -1:
                endcount += 1
                endlist.append(i-1)
            if endcount > 1:
                for j in range(0, x.shape[0]):
                    hasend = False
                    for k in endlist:
                        if x[j, k] == -1:
                            x[j, k] = 0
                            hasend = True
                    if hasend:
                        x[j, max(endlist)] = -1
            endcount = 0
            endlist = []
        elif xends[i] == -1:
            endcount += 1
            endlist.append(i)
    return x

# Combined starts and ends
def showstartend(x):
    start = np.zeros(x.shape[1])
    end = np.zeros(x.shape[1])
    for i in range(0,x.shape[1]):
        for j in range(0,x.shape[0]):
            if x[j,i]==1:
                start[i]+=1
            elif x[j,i]==-1:
                end[i]+=-1
    return (start,end)

# Function creates rest channel (perform after splitting staves and aligning ends)
def rest(x): # To be used on findnotes() output
    a = np.cumsum(x,axis=1)
    b = np.zeros_like(x)
    for i in range(0, x.shape[0]):
        for j in range(1, x.shape[1]):
            if a[i,j]==0 and a[i,j-1]==0:
                b[i,j]=1
    c = np.prod(b,axis=0) # Entry is 1 only if all channels are empty
    d = np.zeros_like(c)
    for j in range(0, x.shape[1]):
        if j == 0:
            d[j] = 0
        elif j == x.shape[1]-1:
            d[j] = -1
        elif c[j] == 1 and c[j-1]==0:
            d[j]=1
        elif c[j]==1 and c[j+1]==0:
            d[j]=-1
    return np.concatenate((x,np.expand_dims(d,axis=0)),axis=0)

# Function turns start and stop into a list of note start times and durations
def tabulate(x): # To be used on findnotes() output with rest channel
    a = starts(x)
    b = ends(x)
    chordlist = []
    currentnotes = []
    notestart = 0
    duration = 0
    for i in range(0,x.shape[1]):
        if a[i]==1:
            if b[i] == -1:
                chordlist.append([notestart, duration, currentnotes])
            notestart = i
            duration = 0
            currentnotes = []
            for j in range(0, x.shape[0]):
                if x[j,i]==1:
                    if j < x.shape[0]-1:
                        currentnotes.append(j)
                    elif j == x.shape[0]-1:
                        currentnotes.append('r')
        elif a[i]==0 and b[i]==0:
            duration +=1
        elif b[i]==-1:
            duration +=1
            chordlist.append([notestart,duration,currentnotes])
    return chordlist

def fillin(chordlist):
    newchordlist = chordlist[:]
    j = 0
    for i in range(len(chordlist)-1):
        if chordlist[i][0]+chordlist[i][1]+1 != chordlist[i+1][0]:
            start = chordlist[i][0]+chordlist[i][1]+1
            end = chordlist[i+1][0]-1
            newchordlist.insert(j+1, [start,end-1-start,['r']])
            j+=1
        j += 1
    return newchordlist

# Allowable note durations
bias = durationbias
durationbins = np.array([[0,1,1.5-bias],
                    [1.5-bias,2,2.5+bias],
                    [2.5+bias,3,3.5-bias],
                    [3.5-bias,4,5+bias],
                    [5+bias,6,7],
                    [7,8,10],
                    [10,12,14],
                    [14,16,20],
                    [20,24,28],
                    [28,32,40],
                    [40,48,56],
                    [56,64,72]])

evendurationbins = np.array([[0,2,3],
                    [3,4,5],
                    [5,6,7],
                    [7,8,10],
                    [10,12,14],
                    [14,16,20],
                    [20,24,28],
                    [28,32,40],
                    [40,48,56],
                    [56,64,72]])

# Function aligns durations in a new column in the chordlist
def subdivide(x1,x2=None,n=1,w=10,guess = None):
    dt = 40/step
    initialtempo = dt
    total = (x1[-1][0] + x1[-1][1])
    cut =  total/n
    cuts = []
    for i in range(0,n): # Splits into n time segments, in case of tempo variability
        if i ==0:
            cuts.append(0)
        else:
            if x2:
                for j in range(int(i * cut), total):
                    if [a for a in x1 if a[0] == j] != [] and [a for a in x2 if a[0] == j] != []:
                        if j not in cuts:
                            cuts.append(j)
                        break
            else:
                for j in range(int(i * cut), total):
                    if [a for a in x1 if a[0] == j] != []:
                        if j not in cuts:
                            cuts.append(j)
                        break
    cuts.append(total+1)
    for i in range(0,n): # Create list of all durations within a time segment
        durationlist = []
        restdurationlist = []
        for x in x1:
            if cuts[i] <= x[0] < cuts[i+1]:
                if x[2]!=['r']:
                    durationlist.append(x[1])
                else:
                    restdurationlist.append(x[1])
        if x2:
            for x in x2:
                if cuts[i] <= x[0] < cuts[i + 1]:
                    if x[2]!=['r']:
                        durationlist.append(x[1])
                    else:
                        restdurationlist.append(x[1])
        def evaluatetempo(): # Evaluate loss function for a tempo
            loss = 0
            bins = dt*durationbins
            for a in restdurationlist:
                loss += (a/dt-round(a/dt))**2
            for a in durationlist:
                for b in bins:
                    if b[0] <= a < b[2]:
                        if b[1] <= 1 or b[1] >= 32: # Penalty for really short and really long notes
                            loss += ((a - b[1]) / max(b[1],dt*6)) ** 2 + 0.1
                        elif b[1]%2 !=0 and b[1]%2 !=0: # Penalty for shorter dotted notes
                            loss += ((a - b[1]) / max(b[1],dt*6)) ** 2 + 0.075
                        elif b[1] >= 16 or b[1]%4 !=0: # Penalty for dotted notes
                            loss += ((a - b[1]) / max(b[1],dt*6)) ** 2 + 0.05
                        else:
                            loss += ((a - b[1]) / max(b[1],dt*6)) ** 2
                        break
            return loss
        minloss = None
        finaltempo = None
        if i == 0: # Evaluate different tempos, and choose the one with minimum loss
            if not guess:
                for j in range(40, 200):
                    dt = j / step
                    tempo = evaluatetempo()
                    if minloss == None or tempo < minloss:
                        minloss = tempo
                        finaltempo = dt
                        initialtempo = j
            else:
                for j in range(int(guess*step-w), int(guess*step+w)):
                    dt = j / step
                    tempo = evaluatetempo()
                    if minloss == None or tempo < minloss:
                        minloss = tempo
                        finaltempo = dt
                        initialtempo = j
        else:
            for j in range(initialtempo-w, initialtempo+w):
                dt = j / step
                tempo = evaluatetempo()
                if minloss == None or tempo < minloss:
                    minloss = tempo
                    finaltempo = dt
                    initialtempo = j
        def bestfitdurations(clist):
            bins = finaltempo * durationbins
            evenbins = finaltempo * evendurationbins
            for a in clist:  # Append new durations onto chord list
                if cuts[i] <= a[0] < cuts[i + 1]:
                    if a[2] != ['r']:
                        for b in bins:
                            if b[0] <= a[1] < b[2]:
                                a.append(b[1] / finaltempo)
                                break
                    else:
                        a.append(round(a[1] / finaltempo))
            oddcount = 0
            for a in clist: # Change unpaired odd durations to even durations
                if cuts[i] <= a[0] < cuts[i + 1]:
                    if a[3] % 2 != 0:
                        oddcount = oddcount % 2
                        oddcount += 1
                    else:
                        oddcount = 0
                    if clist.index(a)<len(clist)-1:
                        if oddcount == 1 and clist[clist.index(a) + 1][3] % 2 == 0:
                            if a[2] != ['r']:
                                for b in evenbins:
                                    if b[0] <= a[1] < b[2]:
                                        a[3] = (b[1] / finaltempo)
                                        break
                            else:
                                a[3] = round(a[1] / finaltempo / 2) * 2
        bestfitdurations(x1)
        if x2:
            bestfitdurations(x2)
        if i == 0:
            firsttempo = finaltempo
    return firsttempo

# Adjusts duration to align with beats
def adjustduration(x,gain=10,window=10): # Input aligned chordlist
    a = []
    for b in x:
        a.append(b[3])
    a = np.array(a)
    def checkalignment(y):
        score = 0
        c = np.cumsum(y)
        for d in c: # Higher score if aligned with beat
            if d%2 == 0:
                score += 1/16
            if d%4 ==0:
                score += 1/8
            if d%8 ==0:
                score += 1/4
            if d%16 ==0 or d%24 ==0:
                score += 1/2
            if d%32 ==0 or d%48 ==0:
                score += 1
        return score
    currentscore = checkalignment(a)
    optimum = a[0]
    for i in range(0,32):
        a[0]=i
        alignment = checkalignment(a)
        if alignment > currentscore:
            currentscore = alignment
            optimum = i
    a[0]=optimum
    for i in range(1,len(a)):
        if x[i][2] != ['r']: # Adjust length of rests if alignment improves more than a threshold (gain)
            currentscore = checkalignment(a)
            shortalignment  = 0
            longalignment  = 0
            for i in range(0,len(durationbins)):
                if a[i] == durationbins[i, 1]:
                    if 9 > i > 2:
                        a[i] = durationbins[i - 1, 1]
                        shortalignment = checkalignment(a)
                    if 8 > i > 0:
                        a[i] = durationbins[i + 1, 1]
                        longalignment = checkalignment(a)
                    if longalignment > shortalignment and longalignment - currentscore > gain:
                        a[i]=durationbins[i + 1, 1]
                    elif longalignment < shortalignment and shortalignment - currentscore > gain:
                        a[i] = durationbins[i - 1, 1]
                    else:
                        a[i]= durationbins[i, 1]
        else: # Adjust length of notes if alignment improves more than a threshold (gain)
            optimum = a[i]
            currentscore = checkalignment(a)
            bestscore = currentscore
            for j in range(-1*window,window+1):
                a[i] += 0.5*j
                alignment  = checkalignment(a)
                if alignment > bestscore:
                    bestscore = alignment
                    optimum = a[i]
                a[i] -= 0.5 * j
            if bestscore - currentscore > gain:
                a[i] = optimum
    newstarts = np.concatenate((np.zeros(1),np.cumsum(a)))
    for i in range(0,len(a)):
        x[i][3]=a[i]
        x[i].append(newstarts[i])


def trackadjust(x,combinedx): # Align treble and bass with adjusted combined chordlist
    x[0][3] = [b[3] for b in combinedx if b[0]==x[0][0]][0]
    for a in x:
        if [b[3] for b in combinedx if b[0]==a[0]]:
            if [b[3] for b in combinedx if b[0] == a[0]][0] > a[3] and a[2]!=['r']:
                a[3] = [b[3] for b in combinedx if b[0] == a[0]][0]
            a.append([b[4] for b in combinedx if b[0]==a[0]][0])
    for a in x:
        if x.index(a)!= len(x)-1 and x.index(a)!=0:
            if not [b[3] for b in combinedx if b[0] == a[0]]:
                a.append(x[x.index(a) - 1][4] + x[x.index(a) - 1][3])
                a[3] = x[x.index(a) + 1][4] - a[4]
            elif a[2] == ['r']:
                a[4]=x[x.index(a) - 1][4] + x[x.index(a) - 1][3]
                a[3] = x[x.index(a) + 1][4] - a[4]
        elif x.index(a)== len(x)-1:
            if not [b[3] for b in combinedx if b[0] == a[0]]:
                a.append(x[x.index(a) - 1][4] + x[x.index(a) - 1][3])
                a[3] = 8
            elif a[2] == ['r']:
                a[4]=x[x.index(a) - 1][4] + x[x.index(a) - 1][3]
                a[3] = 8

# Meter Detection
def meterdetect(x):
    a = []
    for b in x:
        a.append(b[3])
    a = np.array(a)
    score4 = 0
    score3 = 0
    c = np.cumsum(a)
    for d in c:
        if d % 16 == 0:
            score4 += 1/2
        if d % 12 == 0:
            score3 += 1/2
        if d % 32 == 0:
            score4 += 1
        if d % 24 == 0:
            score3 += 1
    if score3/score4 > 1.5:
        return 3
    else:
        return 4

# Scale Basis
majorfilt = [[1,0,1,0,1,1,0,1,0,1,0,1],
 [1,1,0,1,0,1,1,0,1,0,1,0],
 [0,1,1,0,1,0,1,1,0,1,0,1],
 [1,0,1,1,0,1,0,1,1,0,1,0],
 [0,1,0,1,1,0,1,0,1,1,0,1],
 [1,0,1,0,1,1,0,1,0,1,1,0],
 [0,1,0,1,0,1,1,0,1,0,1,1],
 [1,0,1,0,1,0,1,1,0,1,0,1],
 [1,1,0,1,0,1,0,1,1,0,1,0],
 [0,1,1,0,1,0,1,0,1,1,0,1],
 [1,0,1,1,0,1,0,1,0,1,1,0],
 [0,1,0,1,1,0,1,0,1,0,1,1]]

minorfilt = [[1,0,1,1,0,1,0,0.5,0.5,0.5,0.5,1],
 [1,1,0,1,1,0,1,0,0.5,0.5,0.5,0.5],
 [0.5,1,1,0,1,1,0,1,0,0.5,0.5,0.5],
 [0.5,0.5,1,1,0,1,1,0,1,0,0.5,0.5],
 [0.5,0.5,0.5,1,1,0,1,1,0,1,0,0.5],
 [0.5,0.5,0.5,0.5,1,1,0,1,1,0,1,0],
 [0,0.5,0.5,0.5,0.5,1,1,0,1,1,0,1],
 [1,0,0.5,0.5,0.5,0.5,1,1,0,1,1,0],
 [0,1,0,0.5,0.5,0.5,0.5,1,1,0,1,1],
 [1,0,1,0,0.5,0.5,0.5,0.5,1,1,0,1],
 [1,1,0,1,0,0.5,0.5,0.5,0.5,1,1,0],
 [0,1,1,0,1,0,0.5,0.5,0.5,0.5,1,1]]

# Triad Basis
majortriad = [[2,0,0,0,1,0,0,1.5,0,0,0,0],
 [0,2,0,0,0,1,0,0,1.5,0,0,0],
 [0,0,2,0,0,0,1,0,0,1.5,0,0],
 [0,0,0,2,0,0,0,1,0,0,1.5,0],
 [0,0,0,0,2,0,0,0,1,0,0,1.5],
 [1.5,0,0,0,0,2,0,0,0,1,0,0],
 [0,1.5,0,0,0,0,2,0,0,0,1,0],
 [0,0,1.5,0,0,0,0,2,0,0,0,1],
 [1,0,0,1.5,0,0,0,0,2,0,0,0],
 [0,1,0,0,1.5,0,0,0,0,2,0,0],
 [0,0,1,0,0,1.5,0,0,0,0,2,0],
 [0,0,0,1,0,0,1.5,0,0,0,0,2]]

minortriad = [[2,0,0,1,0,0,0,1.5,0,0,0,0],
 [0,2,0,0,1,0,0,0,1.5,0,0,0],
 [0,0,2,0,0,1,0,0,0,1.5,0,0],
 [0,0,0,2,0,0,1,0,0,0,1.5,0],
 [0,0,0,0,2,0,0,1,0,0,0,1.5],
 [1.5,0,0,0,0,2,0,0,1,0,0,0],
 [0,1.5,0,0,0,0,2,0,0,1,0,0],
 [0,0,1.5,0,0,0,0,2,0,0,1,0],
 [0,0,0,1.5,0,0,0,0,2,0,0,1],
 [1,0,0,0,1.5,0,0,0,0,2,0,0],
 [0,1,0,0,0,1.5,0,0,0,0,2,0],
 [0,0,1,0,0,0,1.5,0,0,0,0,2]]

# Note dictionary
tonedict = {0:'C',1:'C#/Db',2:'D',3:'D#/Eb',4:'E',5:'F',6:'F#/Gb',7:'G',8:'G#/Ab',9:'A',10:'A#/Bb',11:'B'}
tonicdict = {0:'c',1:'cs',2:'d',3:'ef',4:'e',5:'f',6:'gf',7:'g',8:'af',9:'a',10:'bf',11:'b'}

# Chromagram average value
def avgval(x):
    a = np.average(x,axis=1)
    a = np.transpose(a)
    if len(a)//12 != 0:
        a = np.concatenate((a,np.zeros(12-len(a)%12)))
    a = np.hsplit(a,len(a)/12)
    b = np.zeros(12)
    for x in a:
        b+=x
    b = np.concatenate((b[4:],b[:4]))
    return b

# Frequency of each tonic note is modeled as a linear combination of uniform distribution of all notes,
# uniform distribution of notes in scale, and triad notes
def findkey(chromagram):
    tonesummary = avgval(chromagram)
    majormax = 0
    majorkey = None
    for i in range(0, 12):
        X = np.transpose(np.vstack((np.ones(12), majorfilt[i], majortriad[i])))
        y = np.transpose(tonesummary)
        model = linear_model.LinearRegression()
        model.fit(X, y)
        ypred = model.predict(X)
        a = r2_score(y, ypred)
        if a > majormax:
            majormax = a
            majorkey = tonedict[i]
            majortonic = tonicdict[i]
    minormax = 0
    minorkey = None
    for i in range(0, 12):
        X = np.transpose(np.vstack((np.ones(12), minorfilt[i], minortriad[i])))
        y = np.transpose(tonesummary)
        model = linear_model.LinearRegression()
        model.fit(X, y)
        ypred = model.predict(X)
        a = r2_score(y, ypred)
        if a > minormax:
            minormax = a
            minorkey = tonedict[i]
            minortonic =tonicdict[i]
    if majormax >= minormax:
        print(majorkey + ' Major')
        return(majortonic,'major')
    else:
        print(minorkey + ' Minor')
        return(minortonic,'minor')

# Analysis Procedure

chromagram = chromagraph(analysisstart,analysisstop,analysisstep)

chromacombined = findnotes(chromagram)

chromacombined = removeshort(chromacombined,shortthreshold)

chromacombined = alignstart(chromacombined,alignthreshold)

# Splits the treble and bass tones
stavesplit = 60+88
chromatop = chromacombined[stavesplit:,:]
chromabottom = chromacombined[:stavesplit,:]

chromacombined = alignends(chromacombined,alignendsthreshold)
chromatop = alignends(chromatop,alignendsthreshold)
chromabottom = alignends(chromabottom,alignendsthreshold)

chromacombined = rest(chromacombined)
chromatop = rest(chromatop)
chromabottom = rest(chromabottom)

combinedlist = tabulate(chromacombined)
toplist = tabulate(chromatop)
bottomlist = tabulate(chromabottom)

for a in toplist:
    for i in range(0,len(a[2])):
        if a[2][i]!='r':
            a[2][i] += stavesplit

combinedlist = fillin(combinedlist)
tempo = subdivide(combinedlist,n=subdivisions,w=evaluationwindow)
subdivide(toplist,bottomlist,n=subdivisions,w=evaluationwindow,guess=tempo)
adjustedcombined = adjustduration(combinedlist,gain=restadjustmentgain,window=adjustmentwindow)

trackadjust(toplist,combinedlist)
trackadjust(bottomlist,combinedlist)

def removezeroes(x):
    for a in x:
        if a[3]==0:
            x.remove(a)
    for a in x: # To remove duplicate entries if any
        if a[3]==0:
            x.remove(a)

removezeroes(combinedlist)
removezeroes(toplist)
removezeroes(bottomlist)

# Plot amplitude of each pitch vs. time
def plotstaff(cgram,clist):
    toneset = set()
    for x in clist:
        if x[2] !=['r']:
            toneset = toneset.union(x[2])
    for x in toneset:
        plt.plot(time,cgram[x])

# Plot note start and end vs. time
def plotnotes(cgram,clist):
    toneset = set()
    for x in clist:
        if x[2] !=['r']:
            toneset = toneset.union(x[2])
    notes = np.cumsum(cgram, axis=1)
    for x in toneset:
        plt.plot(time,10**7*notes[x])

plotstaff(chromagram,combinedlist)
plt.title('Note Plot')
plt.xlabel('Time (ms)')
plt.ylabel('Signal')

# Duration conversion
def convertduration(x):
    x *= 2
    denominator = 64
    while x%2==0:
        x/=2
        denominator/=2
    return (x,denominator)

# Simplify fraction
def simplifyfraction(n,d):
    while n%2==0:
        n/=2
        d/=2
    return (n,d)

# Assignability List
assignable = [1,2,3,4,6,7,8,12,14,15,16,24,28,30,31,32,48,56,60,62,63,64]

# For non-assignable rest durations, split to two assignable durations
def splitduration(x):
    if x not in assignable:
        first = 0
        second = 0
        for a in assignable:
            if x-a in assignable:
                first = a
                second = x-a
                break
        return (first,second)

# Lists Notes and Chords
def listnotes(x): # Input a chord list
    notelist = []
    for a in x:
        if a[2]==['r']:
            d = convertduration(a[3])
            if d[0] not in assignable:
                splitd = splitduration(d[0])
                duration1 = simplifyfraction(splitd[0],d[1])
                duration2 = simplifyfraction(splitd[1],d[1])
                notelist.append(ab.Rest(ab.Duration(*duration1)))
                notelist.append(ab.Rest(ab.Duration(*duration2)))
            else:
                notelist.append(ab.Rest(ab.Duration(*d)))
        elif len(a[2])==1:
            notelist.append(ab.Note(a[2][0]-148,ab.Duration(*convertduration(a[3]))))
        elif len(a[2])>1:
            chordnotes = []
            for b in a[2]:
                chordnotes.append(b-148)
            notelist.append(ab.Chord(chordnotes,ab.Duration(*convertduration(a[3]))))
    return notelist

# Convert chordlists to musical score using Abjad
keysig = findkey(chromagram)
ksignature = ab.KeySignature(*keysig)

timesig = meterdetect(combinedlist)
tsignature = ab.TimeSignature((timesig,4))

def treblebass():
    trebleclef = ab.Clef('treble')
    treblestaff = ab.Staff(listnotes(toplist))
    ab.attach(trebleclef, treblestaff[0])
    ab.attach(ksignature, treblestaff[0])
    ab.attach(tsignature, treblestaff[0])

    bassclef = ab.Clef('bass')
    bassstaff = ab.Staff(listnotes(bottomlist))
    ab.attach(bassclef, bassstaff[0])
    ab.attach(ksignature, bassstaff[0])
    ab.attach(tsignature, bassstaff[0])

    group = ab.StaffGroup([treblestaff, bassstaff])
    ab.show(group)

def treble():
    trebleclef = ab.Clef('treble')
    treblestaff = ab.Staff(listnotes(combinedlist))
    ab.attach(trebleclef, treblestaff[0])
    ab.attach(ksignature, treblestaff[0])
    ab.attach(tsignature, treblestaff[0])
    ab.show(treblestaff)

def bass():
    bassclef = ab.Clef('bass')
    bassstaff = ab.Staff(listnotes(combinedlist))
    ab.attach(bassclef, bassstaff[0])
    ab.attach(ksignature, bassstaff[0])
    ab.attach(tsignature, bassstaff[0])
    ab.show(bassstaff)

# Plot Chromagram
fig, ax = plt.subplots()
ax.contourf(time,tones[88:],chromagram[88:,:],np.linspace(0,chromagram.max()//2,100),extend='both')
ax.set_facecolor('#440154')
ax.set_title('Chromagram')
ax.set_xlabel('Time (ms)')
ax.set_ylabel('MIDI Pitch Number')
plt.show()

# Generate score
if analysisstaves == 'Treble+Bass':
    treblebass()
elif analysisstaves == 'Bass':
    bass()
else:
    treble()

