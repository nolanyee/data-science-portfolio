'''
This program generates a depth map from an image of matte monochromatic bas-relief.
The algorithm uses physical principles of light to calculate a normal map, which is integrated to a depth map.
'''

import scipy.ndimage
import scipy.stats
import scipy.misc
import math
import imageio
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from skimage.transform import resize
from tkinter import *
from tkinter.ttk import *

# Graphic User Interface for Parameter Settings

loopactive=True
window = Tk(className=' Settings')
frame = Frame(window,width=1200, height=800)
frame.pack(fill=BOTH, expand=True )

def parameterfield(name,description,w,default,r, offset=0):
    globals().update({name+'label':Label(frame,text=description)})
    globals().update({name + 'entry': Entry(frame, width=w)})
    globals()[name + 'entry'].insert(0,default)
    globals()[name + 'label'].grid(row=r, column = 0+offset, sticky=E)
    globals()[name + 'entry'].grid(row=r, column = 1+offset, sticky=W)

parameterfield('imagename','Input Image Filename',80,'',1)

headinglabel1 = Label(frame, text='LIGHT ANGLE ANALYSIS')
headinglabel1.grid(row=2, column=0, sticky=E)

parameterfield('sobel_wt','Weight of Total Sobel Magnitude',5,0.5,3)
parameterfield('adjacent_SS_wt','Weight of Adjacent Sum of Squares',5,1.5,4)
parameterfield('theta_intervals','Number of Scanning Angles',5,32,5)
parameterfield('theta_override','Override Light Angle',5,'None',6)

headinglabel2 = Label(frame, text='RELIEF PLANE DETECTION')
headinglabel2.grid(row=7, column=0, sticky=E)

parameterfield('flat_width','Tolerance for Contiguous Region',5,5,8)
parameterfield('flat_smoothing','Smoothing Factor',5,100,9)
parameterfield('flat_override','Override Relief Plane Intensity',5,'None',10)

headinglabel3 = Label(frame, text='CAST SHADOW DETECTION')
headinglabel3.grid(row=11, column=0, sticky=E)

castshadowlabel = Label(frame, text='Cast Shadow')
castshadowvar= StringVar()
castshadowcombo = Combobox(frame, textvariable=castshadowvar)
castshadowcombo['values']=['True', 'False']
castshadowvar.set('True')
castshadowlabel.grid(row=12, column=0, sticky=E)
castshadowcombo.grid(row=12, column=1, sticky=W)

secondary_lightlabel = Label(frame, text='Secondary Light Type')
secondary_lightvar= StringVar()
secondary_lightcombo = Combobox(frame, textvariable=secondary_lightvar)
secondary_lightcombo['values']=['reflected', 'ambient']
secondary_lightvar.set('reflected')
secondary_lightlabel.grid(row=13, column=0, sticky=E)
secondary_lightcombo.grid(row=13, column=1, sticky=W)

parameterfield('midtone_override','Override Midtone Intensity',5,'None',14)
parameterfield('shadow_drop_width_start','Shadow Drop Width',5,250,15)
parameterfield('shadow_drop_width_end','Shadow Rise Width',5,50,16)
parameterfield('shadow_drop_height','Shadow Drop Height Threshold',5,0.4,17)
parameterfield('shadow_rise_height','Shadow Rise Height Threshold',5,0.3,18)
parameterfield('shadow_threshold_fraction','Cast Shadow Area Threshold (Fraction)',5,0.98,19)
parameterfield('shadow_override','Override Cast Shadow Intensity',5,'None',20)

headinglabel4 = Label(frame, text='IMAGE INTENSITY OFFSETS')
headinglabel4.grid(row=21, column=0, sticky=E)

parameterfield('shadow_min_offset','Offset Shadow Minimum',5,0,22)
parameterfield('shadow_max_offset','Offset Shadow Maximum',5,0,23)

parameterfield('light_min_offset','Offset Light Minimum',5,0,24)
parameterfield('light_max_offset','Offset Light Maximum',5,0,25)

headinglabel7 = Label(frame, text='RELIEF TYPE')
headinglabel7.grid(row=26, column=0, sticky=E)

typelabel = Label(frame, text='Relief Type')
typevar= StringVar()
typecombo = Combobox(frame, textvariable=typevar)
typecombo['values']=['convex','concave']
typevar.set('convex')
typelabel.grid(row=27, column=0, sticky=E)
typecombo.grid(row=27, column=1, sticky=W)

headinglabel5 = Label(frame, text='SOBEL MAP SMOOTHING')
headinglabel5.grid(row=28, column=0, sticky=E)

parameterfield('sobel_smooth_factor','Sobel Map Smoothing Factor',5,0,29)
parameterfield('sobel_neighbors_threshold','Sobel Magnitude Threshold',5,0.0,30)

headinglabel6 = Label(frame, text='DISPLACEMENT MAP PROCESSING')
headinglabel6.grid(row=31, column=0, sticky=E)

parameterfield('displace_threshold','Displacement Magnitude Threshold',5,10,32)
parameterfield('smooth_threshold','Sobel Magnitude Threshold',5,0.01,33)
parameterfield('smooth_factor','Displacement Smoothing Factor',5,2,34)

headinglabel6 = Label(frame, text='DEPTH MAP GENERATION')
headinglabel6.grid(row=35, column=0, sticky=E)

integration_algorithmlabel = Label(frame, text='Normal Map Integration Algorithm')
integration_algorithmvar= StringVar()
integration_algorithmcombo = Combobox(frame, textvariable=integration_algorithmvar)
integration_algorithmcombo['values']=['rotation', 'iterative']
integration_algorithmvar.set('iterative')
integration_algorithmlabel.grid(row=36, column=0, sticky=E)
integration_algorithmcombo.grid(row=36, column=1, sticky=W)

parameterfield('integration_fold','Number of Angles for Rotation',5,90,37)
parameterfield('initial_iterations','Initial Iterations',5,10,38)
parameterfield('final_iterations','Final Iterations',5,200,39)

bias_complexitylabel = Label(frame, text='Bias Complexity')
bias_complexityvar= StringVar()
bias_complexitycombo = Combobox(frame, textvariable=bias_complexityvar)
bias_complexitycombo['values']=['linear', 'quadratic']
bias_complexityvar.set('linear')
bias_complexitylabel.grid(row=40, column=0, sticky=E)
bias_complexitycombo.grid(row=40, column=1, sticky=W)

parameterfield('final_smooth_threshold','Smoothing Sobel Magnitude Threshold',5,0.5,41)
parameterfield('final_smooth_factor','Sobel Masked Smoothing Factor',5,1.6,42)
parameterfield('full_smooth_factor','Overall Smoothing Factor',5,0.5,43)

parameterfield('normaloutput','Normal Map Output File Path',80,'',44)
parameterfield('depthoutput','Depth Map Output File Path',80,'',45)

# OK button escapes loop

def done():
    global loopactive
    window.update_idletasks()
    window.withdraw()
    loopactive = False
okbutton =Button(frame, text='OK', command=done)

okbutton.grid(row=46, column = 1, sticky = W)

while loopactive:
    window.update()

# PARAMETER SETTING

# Light Angle
sobel_wt = float(sobel_wtentry.get()) # Weight for penalizing gradient in a particular direction, recommend 0.5
adjacent_SS_wt = float(adjacent_SS_wtentry.get()) # Weight for parallelism of slices, recommend 1.5
theta_intervals = int(theta_intervalsentry.get()) # Number of angles to scan through, recommend 32

if theta_overrideentry.get() == 'None': # Manually override light angle detection result
    theta_override = None
else:
    theta_override = float(theta_overrideentry.get())

# Flat Surface Intesity
flat_width = int(flat_widthentry.get()) # Resolution, between 0 and 100, recommend 5

# Moving average window = image size / smoothing, recommend between 10-100
flat_smoothing = int(flat_smoothingentry.get())

if flat_overrideentry.get() == 'None': # Manually override flat value
    flat_override = None
else:
    flat_override = float(flat_overrideentry.get())

# Cast Shadow
if castshadowvar.get() =='True':
    cast_shadow = True
else:
    cast_shadow = False

secondary_light = secondary_lightvar.get()

if midtone_overrideentry.get() == 'None': # override midtone value, by default it is the flat surface intensity
    midtone_override = None
else:
    midtone_override = float(midtone_overrideentry.get())

# intensity drop detection window is image size / drop width, recommend 250
shadow_drop_width_start = int(shadow_drop_width_startentry.get())

# intensity step detection window is image size / drop width, recommend 50
shadow_drop_width_end = int(shadow_drop_width_endentry.get())

# threshold size of intensity drop, between 0 and 1, recommend 0.4
shadow_drop_height = float(shadow_drop_heightentry.get())

# threshold size of intensity step, between 0 and 1, recommend 0.3
shadow_rise_height = float(shadow_rise_heightentry.get())

# percentage of shadow values under the shadow threshold, default 0.98
shadow_threshold_fraction = float(shadow_threshold_fractionentry.get())

if shadow_overrideentry.get() == 'None': # manually override shadow threshold
    shadow_override = None
else:
    shadow_override = float(shadow_overrideentry.get())

# Shadow Calculations
shadow_min_offset = float(shadow_min_offsetentry.get()) # Positive offset size for shadow minimum value
shadow_max_offset = float(shadow_max_offsetentry.get()) # Negative offset size for shadow maximum value

# Light Calculations
light_min_offset = float(light_min_offsetentry.get()) # Positive offset size for light minimum value
light_max_offset = float(light_max_offsetentry.get()) # Negative offset size for light maximum value

# Gradient Map Neighbors Imputation
sobel_smooth_factor = float(sobel_smooth_factorentry.get()) # Smoothing applied before Sobel filter is applied

# Threshold Sobel magnitude under which gradient direction is imputed
sobel_neighbors_threshold = float(sobel_neighbors_thresholdentry.get())

# Relief Type
relief_type = typevar.get()

# Displacement Map Generation
displace_threshold = float(displace_thresholdentry.get()) # Maximum magnitude of displacement per pixel, recommend 5
smooth_threshold =float(smooth_thresholdentry.get()) # Sobel magnitude under which displacement map is smoothed
smooth_factor = float(smooth_factorentry.get()) # Gaussian smoothing parameter, recommend 2

# Depth Map Generation
integration_algorithm = integration_algorithmvar.get() # Either 'rotation' or 'iterative'
integration_fold = int(integration_foldentry.get()) # Number of directions integration is performed, recommend 90
initial_iterations = int(initial_iterationsentry.get()) # Number of iterations for upper levels of pyramid
final_iterations = int(final_iterationsentry.get()) # Number of iterations for bottom level of pyramid
bias_complexity = bias_complexityvar.get() # Model for depth map bias, 'linear' or 'quadratic', recommend 'linear'

# Sobel magnitude under which depth map is smoothed, recommend 0.6
final_smooth_threshold = float(final_smooth_thresholdentry.get())
final_smooth_factor = float(final_smooth_factorentry.get()) # Gaussian smoothing parameter, recommend 2
full_smooth_factor =float(full_smooth_factorentry.get()) # Final smoothing over unmasked image

imagename = imagenameentry.get()
normaloutput =normaloutputentry.get()
depthoutput = depthoutputentry.get()

window.destroy()

# PROCEDURES
# Load image and convert to grayscale
image = imageio.imread(imagename, as_gray = True)/255

# Shear image (this function is reversible without introducing any noise)
def shear(image, slope, horizontal = True):
    image = image[:, ~np.all(np.isnan(image), axis=0)]
    image = image[~np.all(np.isnan(image), axis=1), :]
    h = image.shape[0]
    w = image.shape[1]
    if horizontal:
        if slope >= 0:
            expanded = np.full((h,round(w+slope*h)),np.nan)
            for i in range(h):
                expanded[i,round(slope*i):(round(slope*i)+w)]=image[i,:]
        else:
            expanded = np.full((h, round(w - slope * h)), np.nan)
            for i in range(h):
                expanded[i, round(-1*slope*h)-round(-1*slope*i):(round(-1*slope*h)-round(-1*slope*i) + w)] = image[i, :]
    else:
        if slope >= 0:
            expanded = np.full((round(h + slope * w), w), np.nan)
            for i in range(w):
                expanded[round(slope*i):(round(slope*i)+h),i]=image[:,i]
        else:
            expanded = np.full((round(h - slope * w), w), np.nan)
            for i in range(w):
                expanded[round(-1*slope*w)-round(-1*slope*i):(round(-1*slope*w)-round(-1*slope*i) + h), i] = image[:, i]
    expanded = expanded[:, ~np.all(np.isnan(expanded), axis=0)]
    expanded = expanded[~np.all(np.isnan(expanded), axis=1), :]
    return expanded

# Rotate image using 3 shears
def rotate(image, angle):
    transformed = shear(image, math.tan(angle/2),horizontal=True)
    transformed = shear(transformed, -1*math.sin(angle), horizontal = False)
    transformed = shear(transformed, math.tan(angle/2), horizontal=True)
    return transformed

# Calculate column-wise sum of squared deviations from mean
def ss(image):
    return np.nansum((image-np.nanmean(image, axis=0)[np.newaxis,:])**2),\
           np.nansum((image-np.nanmean(image, axis=1)[:,np.newaxis])**2)

# Calculate column-wise sum of squared deviations from adjacent column
def adjss(image):
    totalss = 0
    for i in range(image.shape[1]-1):
        a=image[:,i]
        b=image[:,i+1]
        mask = np.logical_or(np.isnan(a), np.isnan(b))
        if np.sum(1-mask)>0:
            totalss += np.dot(a[~mask]-b[~mask],a[~mask]-b[~mask])
    return totalss

# Scale results
def scale(x):
    vector = np.array(x)
    return (vector - min(vector))/(max(vector)-min(vector))

# Normalize results
def normalize(x):
    vector = np.array(x)
    return vector / max(vector)

# Incrementally rotate image and calculate sum of squares and derivatives
def theta(image, n):
    angles = []
    parallel = []
    sobely = []
    adjacentss = []
    for angle in [i*math.pi/(n) for i in range(n)]:
        angles.append(angle)
        rotated = rotate(image,angle)
        sobelparallel = np.nansum(scipy.ndimage.sobel(rotated,axis=0)**2)
        ssangle = ss(rotated)
        adjacentsumsq =adjss(rotated)
        parallel.append(ssangle[0])
        sobely.append(sobelparallel)
        adjacentss.append(adjacentsumsq)
    return [angles, parallel, sobely, adjacentss]

# Desirability function for light angle determination
def f(scanresult, sobelwt, adjsswt):
    return scale(scanresult[1])*scale([-1*x for x in scanresult[3]])**adjsswt/normalize(scanresult[2])**sobelwt

# Estimate light angle
def lightangle(scanresult):
    angles = scanresult[0]
    results = f(scanresult, sobel_wt, adjacent_SS_wt)
    matrix = np.array([angles, results])
    filteredmatrix = matrix[:,matrix[1,:]>= 0.95*max(matrix[1,:])]
    return np.mean(filteredmatrix[0,:])

# Calculate moving average of a vector
def movingavg(vector, n):
    vector1 = np.nan_to_num(vector)
    padded = np.append(np.append(np.full(n//2,vector1[0]),vector1), np.full(n//2,vector1[-1]))
    cumulative = np.append(np.array([0]),np.cumsum(padded))
    avg = (cumulative[n:]-cumulative[:-n])/n
    if len(vector) != len(avg):
        avg = avg[1:]
    return avg[~np.isnan(vector)]

# Store the longest contiguous pixel window along the direction of the light, for each slice
def findflat(image, smoothing, width):
    n = min(image.shape)//smoothing
    totalcounts = np.zeros(91)
    for i in range(image.shape[1]):
        vector = movingavg(image[:,i],n)
        countvector = []
        for j in range(width,101-width):
            window = [(j-width)/100, (j+width)/100]
            countmax = 0
            counter = 0
            for k in vector:
                if k >= window[0] and k <= window[1]:
                    counter += 1
                    if counter > countmax:
                        countmax = counter
                else:
                    counter = 0
            countvector.append(countmax)
        totalcounts += np.array(countvector)
    return totalcounts

# Find shadow pixels by detecting drops and steps in pixel intensity
def findshadow(image, dropwidthstart,dropwidthend, dropheight, riseheight, midtone, mask=False):
    imagerange = np.nanmax(image)-np.nanmin(image)
    pixelwidthstart = max(min(image.shape)//dropwidthstart,2)
    pixelwidthend = max(min(image.shape) // dropwidthend,2)
    shadows = []
    if mask:
        shadowmask = np.zeros_like(image)
    for i in range(image.shape[1]):
        vector = image[:,i]
        collect = False
        for j in range(len(vector)-2*pixelwidthstart):
            if vector[j]-min(vector[j+1:j+pixelwidthstart]) >= dropheight*imagerange and \
                min(vector[j+1:j+pixelwidthstart]) < midtone:
                if not collect:
                    collect = True
                    k = j+list(vector[j+1:j+pixelwidthstart]).index(min(vector[j+1:j+pixelwidthstart]))+1
                else:
                    k += 1
            else:
                if not collect:
                    k = j+pixelwidthstart
                else:
                    k += 1
            if max(vector[k+1:k+pixelwidthend])-vector[k]>= riseheight*imagerange:
                collect = False
            if collect:
                if not np.isnan(vector[k]):
                    shadows.append(vector[k])
                if mask:
                    shadowmask[k,i]=1
    if mask:
        shadowmask[np.isnan(image)] = np.nan
        return shadows, shadowmask
    else:
        return shadows

# Clean up any high frequncy artifacts in the shadow mask(shadow where most neighboring pixels are not shadow)
def maskclean(inputmask):
    mask = np.nan_to_num(inputmask)
    h = mask.shape[0]
    w = mask.shape[1]
    center = np.vstack((np.zeros((1, w+2)),np.hstack((np.zeros((h,1)), mask, np.zeros((h,1)))),np.zeros((1, w+2))))
    topleft = np.vstack((np.hstack((mask, np.zeros((h, 2)))), np.zeros((2,w+2))))
    topcenter = np.vstack((np.hstack((np.zeros((h,1)), mask, np.zeros((h,1)))), np.zeros((2,w+2))))
    topright =np.vstack((np.hstack((np.zeros((h, 2)), mask)), np.zeros((2,w+2))))
    leftcenter =np.vstack((np.zeros((1, w+2)),np.hstack((mask, np.zeros((h, 2)))),np.zeros((1, w+2))))
    rightcenter =np.vstack((np.zeros((1, w+2)),np.hstack((np.zeros((h, 2)), mask)),np.zeros((1, w+2))))
    bottomleft =np.vstack((np.zeros((2,w+2)), np.hstack((mask, np.zeros((h, 2))))))
    bottomcenter = np.vstack((np.zeros((2,w+2)), np.hstack((np.zeros((h,1)), mask, np.zeros((h,1))))))
    bottomright =np.vstack((np.zeros((2,w+2)), np.hstack((np.zeros((h, 2)), mask))))
    neighbors = topleft + topcenter + topright +leftcenter +rightcenter +bottomleft +bottomcenter +bottomright
    cleanedmask = np.where((neighbors<=2)&(center==1),0,center)
    cleanedmask = np.where((neighbors>=6)&(center==0),1,cleanedmask)
    cleanedmask = cleanedmask[1:-1,1:-1]
    cleanedmask[np.isnan(inputmask)] = np.nan
    return cleanedmask

# CALCULATING EQUATION CONSTANTS

# Light Angle Scanning
scantheta = theta(image,theta_intervals)
direction = lightangle(scantheta)
if not theta_override is None:
    direction = theta_override

# Calculation of Flat Intensity
flatvector = findflat(rotate(image, direction), flat_smoothing, flat_width)
if flat_override is None:
    pflat = ((np.where(flatvector == max(flatvector))[0]+flat_width)/100)[0]
else:
    pflat = flat_override

# Midtone Calculation
if midtone_override is None:
    midtone = pflat
else:
    midtone = midtone_override

# Shadow Mask Calculation
shadow = findshadow(rotate(image, direction), shadow_drop_width_start, shadow_drop_width_end,
                    shadow_drop_height, shadow_rise_height, midtone, mask=True)
shadowmask = maskclean(shadow[1])
shadowmask = rotate(shadowmask,-1*direction)
shadow[0].sort()
shadowthreshold = shadow[0][round(shadow_threshold_fraction*len(shadow[0]))]
shadowmask[image<=shadowthreshold]=1

print('Lighting Detection Results')
print('Light Direction: ', direction/(2*math.pi)*360)
print('Flat Pixel Value:', ((np.where(flatvector == max(flatvector))[0]+flat_width)/100)[0])
print('Shadow Threshold', shadowthreshold)

if not shadow_override is None:
    shadowthreshold = shadow_override
    shadowmask = np.where(image<shadowthreshold, 1, 0)

if not cast_shadow:
    shadowmask=np.zeros_like(shadowmask)
    shadowthreshold = 0

# PREPROCESSING SOBEL MAP

# Sobel Neighbors Imputation
def sobelneighbors(sobel, sobelmag, threshold):
    mask = np.where(sobelmag<threshold,np.nan,sobel)
    h = mask.shape[0]
    w = mask.shape[1]
    while np.sum(np.isnan(mask))>0:
        topleft = np.vstack((np.hstack((mask, np.zeros((h, 2)))), np.zeros((2,w+2))))
        topcenter = np.vstack((np.hstack((np.zeros((h,1)), mask, np.zeros((h,1)))), np.zeros((2,w+2))))
        topright =np.vstack((np.hstack((np.zeros((h, 2)), mask)), np.zeros((2,w+2))))
        leftcenter =np.vstack((np.zeros((1, w+2)),np.hstack((mask, np.zeros((h, 2)))),np.zeros((1, w+2))))
        rightcenter =np.vstack((np.zeros((1, w+2)),np.hstack((np.zeros((h, 2)), mask)),np.zeros((1, w+2))))
        bottomleft =np.vstack((np.zeros((2,w+2)), np.hstack((mask, np.zeros((h, 2))))))
        bottomcenter = np.vstack((np.zeros((2,w+2)), np.hstack((np.zeros((h,1)), mask, np.zeros((h,1))))))
        bottomright =np.vstack((np.zeros((2,w+2)), np.hstack((np.zeros((h, 2)), mask))))
        neighbors = np.array([topleft,topcenter,topright,leftcenter,rightcenter,bottomleft,bottomcenter,bottomright])
        avgneighbors = np.nanmean(neighbors, axis=0)[1:-1,1:-1]
        mask = np.where(np.isnan(mask), avgneighbors, mask)
    return np.nan_to_num(mask)

# SHARED ARRAYS
if sobel_smooth_factor == 0:
    smoothedimage = image
else:
    smoothedimage = scipy.ndimage.gaussian_filter(image,sobel_smooth_factor)
sobelx = -1*scipy.ndimage.sobel(smoothedimage, axis=1)
sobely = -1*scipy.ndimage.sobel(smoothedimage, axis=0)
sobelmag = np.sqrt(sobelx**2+sobely**2)

if sobel_neighbors_threshold == 0:
    dpdx = sobelx
    dpdy = sobely
else:
    dpdx = sobelneighbors(sobelx, sobelmag, sobel_neighbors_threshold)
    dpdy = sobelneighbors(sobely, sobelmag, sobel_neighbors_threshold)
sobelmagnew = np.sqrt(dpdx**2+dpdy**2)

dpdxdpdy = np.nan_to_num(dpdx/dpdy)
dpdydpdx = np.nan_to_num(dpdy/dpdx)
normdpdx = np.nan_to_num(dpdx/sobelmagnew)
normdpdx = np.where(sobelmagnew==0, 0, normdpdx)
normdpdy = np.nan_to_num(dpdy/sobelmagnew)
normdpdy = np.where(sobelmagnew==0, 0, normdpdy)

# Relu function
def relu(array):
    return (array+abs(array))/2

# SHADOW EQUATIONS

# Constants
if cast_shadow:
    shadowmin = min(shadow[0])
    shadowslope = np.max(image[shadowmask == 1]) - shadowmin

    # Offset image
    shadowmaximum = np.max(image[shadowmask == 1])
    shadowadjustimage = np.where((image < shadowmin + shadow_min_offset) & (image > shadowmin), shadowmin, image)
    shadowadjustimage = np.where((image > shadowmaximum - shadow_max_offset) & (image < shadowmaximum),
                                 shadowmaximum,
                                 shadowadjustimage)
    shadowadjustimage = np.where((image < shadowmaximum - shadow_max_offset) &
                                 (image > shadowmin + shadow_min_offset), shadowmin + (shadowmaximum - shadowmin) /
                                 (shadowmaximum - shadow_max_offset - shadowmin - shadow_min_offset) *
                                 (shadowadjustimage - shadowmin - shadow_min_offset),
                                 shadowadjustimage)
    if secondary_light == 'reflected':
        # Constants
        shadowtheta = -1*direction
        sinshadowtheta = np.sin(shadowtheta)
        cosshadowtheta = np.cos(shadowtheta)

        # Truncating gradient
        cospsi = (shadowadjustimage-shadowmin)/shadowslope
        extremeangle = np.arccos(np.where(cospsi > 1, 1, cospsi))
        shadowextremes = np.where(cospsi >(sinshadowtheta*normdpdx+cosshadowtheta*normdpdy),1,0)
        shadowextremex1 = np.sin(shadowtheta+extremeangle)
        shadowextremex2 = np.sin(shadowtheta-extremeangle)
        shadowextremey1 = np.cos(shadowtheta+extremeangle)
        shadowextremey2 = np.cos(shadowtheta-extremeangle)
        shadowextremesim1 = normdpdx*shadowextremex1+normdpdy*shadowextremey1
        shadowextremesim2 = normdpdx*shadowextremex2+normdpdy*shadowextremey2
        if relief_type == 'concave':
            shadowextremesim1 *=-1
            shadowextremesim2 *=-1
        shadowextremex = np.where(shadowextremesim1<shadowextremesim2,shadowextremex2, shadowextremex1)
        shadowextremey = np.where(shadowextremesim1<shadowextremesim2,shadowextremey2, shadowextremey1)
        shadowdpdx = np.where(shadowextremes==1, shadowextremex, dpdx)
        shadowdpdy = np.where(shadowextremes==1, shadowextremey, dpdy)
        shadowdpdxdpdy = np.nan_to_num(shadowdpdx/shadowdpdy)
        shadowdpdydpdx = np.nan_to_num(shadowdpdy/shadowdpdx)

        # Calculating normal vector
        shadownx =np.where(dpdx==0,0,(shadowadjustimage-shadowmin)/(shadowslope*(sinshadowtheta+
                                                                                 cosshadowtheta*shadowdpdydpdx)))
        shadowny =np.where(dpdy==0,0,(shadowadjustimage-shadowmin)/(shadowslope*(sinshadowtheta*shadowdpdxdpdy+
                                                                                 cosshadowtheta)))
        shadownxymag = np.sqrt(shadownx**2 + shadowny**2)
        shadownx = np.where(shadownxymag > 1, np.nan_to_num(shadownx/shadownxymag), shadownx)
        shadowny = np.where(shadownxymag > 1, np.nan_to_num(shadowny/shadownxymag), shadowny)
        shadownz = np.sqrt(relu(1-shadownx**2-shadowny**2))
    else:
        shadownz = (shadowadjustimage - shadowmin)/shadowslope
        shadowny = np.where(dpdy==0, 0, np.sqrt((1-shadownz**2)/(dpdxdpdy**2+1)))
        shadownx = np.where(dpdy==0, np.sqrt(1-shadownz**2), dpdxdpdy*shadowny)
        shadowny *= np.sign(dpdy)*np.sign(shadowny)
        shadownx *= np.sign(dpdx) * np.sign(shadownx)
        if relief_type == 'concave':
            shadowny *= -1
            shadownx *=-1

# LIGHT EQUATIONS

# Constants
lightslope = np.max(image)-shadowthreshold
lz = (pflat - shadowthreshold)/lightslope
lx = np.sin(math.pi-direction)*np.sqrt(1-lz**2)
ly = np.cos(math.pi-direction)*np.sqrt(1-lz**2)
maglxy = np.sqrt(lx**2+ly**2)
directionz = math.atan(lz/maglxy)

# Offset image
lightmaximum = np.max(image)
lightmin =  shadowthreshold
lightadjustimage = np.where((image<lightmin+light_min_offset)&(image>lightmin),lightmin, image)
lightadjustimage = np.where((image>lightmaximum-light_max_offset)&(image<lightmaximum), lightmaximum,
                             lightadjustimage)
lightadjustimage = np.where((image<lightmaximum-light_max_offset)&(image>lightmin+light_min_offset),
                             lightmin+(lightmaximum-lightmin)/
                             (lightmaximum-light_max_offset-lightmin-light_min_offset)*
                             (lightadjustimage-lightmin-light_min_offset),
                             lightadjustimage)

# Truncating gradient
extremez = np.nan_to_num(lz*lightslope/(lightadjustimage-shadowthreshold))
extremez = np.where(extremez >1 ,1, extremez)
extremez = np.where(extremez <-1 ,-1, extremez)

extremexa = lightslope**2*(ly**2+lx**2)
extremexb = 2*lightslope*lx*(extremez*lz*lightslope-(lightadjustimage-shadowthreshold))
extremexc = np.nan_to_num(((lightadjustimage-shadowthreshold)-lightslope*extremez*lz)**2-lightslope**2*ly**2*(1-extremez**2))

extremex1 = (-1*extremexb+np.sqrt(relu(extremexb**2-4*extremexa*extremexc)))/(2*extremexa)
extremex2 = (-1*extremexb-np.sqrt(relu(extremexb**2-4*extremexa*extremexc)))/(2*extremexa)
extremey1 = (lightadjustimage-shadowthreshold-lightslope*(extremez*lz+extremex1*lx))/(lightslope*ly)
extremey2 = (lightadjustimage-shadowthreshold-lightslope*(extremez*lz+extremex2*lx))/(lightslope*ly)

lightcospsi=np.nan_to_num(((lightadjustimage-shadowthreshold)/lightslope-extremez*lz)/(np.sqrt((lx**2+ly**2)*relu(1-extremez**2))))
lightcospsi = np.where(lightcospsi >1, 1, lightcospsi)
lightcospsi = np.where(lightcospsi <-1, -1, lightcospsi)

lightcosphi = (lightadjustimage-shadowthreshold)/lightslope
lightcosphi = np.where(lightcosphi >1,1,lightcosphi)
lightcosphi = np.where(lightcosphi <-1,-1,lightcosphi)
lightphi = np.arccos(lightcosphi)

lightextremes = np.where((directionz + lightphi < math.pi/2)&(lightcospsi>(normdpdx*lx+normdpdy*ly)/maglxy), 1, 0)
lightextremesim1 = normdpdx*extremex1+normdpdy*extremey1
lightextremesim2 = normdpdx*extremex2+normdpdy*extremey2
if relief_type == 'concave':
    lightextremesim1 *= -1
    lightextremesim2 *= -1
lightextremex = np.where(lightextremesim1<lightextremesim2,extremex2, extremex1)
lightextremey = np.where(lightextremesim1<lightextremesim2,extremey2, extremey1)
lightdpdx = np.where(lightextremes==1, lightextremex, dpdx)
lightdpdy = np.where(lightextremes==1, lightextremey, dpdy)
lightdpdxdpdy = np.nan_to_num(lightdpdx/lightdpdy)
lightdpdxdpdy = np.where(lightdpdy == 0, 0, lightdpdxdpdy)

# Calculating normal vector
lightnA = (lightadjustimage-shadowthreshold)/(lz*lightslope)
lightnB = (lx*lightdpdxdpdy+ly)/lz
lightna = lightnB**2+1+lightdpdxdpdy**2
lightnb = -2*lightnA*lightnB
lightnc = lightnA**2-1
lightny1 = (-1*lightnb+np.sqrt(relu(lightnb**2-4*lightna*lightnc)))/(2*lightna)
lightny2 = (-1*lightnb-np.sqrt(relu(lightnb**2-4*lightna*lightnc)))/(2*lightna)
lightny1 = np.where(lightdpdy==0,0,lightny1)
lightny2 = np.where(lightdpdy==0,0,lightny2)

lightxa = lx**2+lz**2
lightxb = -2*lx*(lightadjustimage-shadowthreshold)/lightslope
lightxc = ((lightadjustimage-shadowthreshold)/lightslope)**2-lz**2
lightnx1 = (-1*lightxb+np.sqrt(relu(lightxb**2-4*lightxa*lightxc)))/(2*lightxa)
lightnx2 = (-1*lightxb-np.sqrt(relu(lightxb**2-4*lightxa*lightxc)))/(2*lightxa)

lightnx1 = np.where(lightdpdy==0, lightnx1,lightny1*lightdpdxdpdy)
lightnx2 =  np.where(lightdpdy==0, lightnx2,lightny2*lightdpdxdpdy)

lightnz1 = np.sqrt(relu(1-lightny1**2-lightnx1**2))
lightnz2 = np.sqrt(relu(1-lightny2**2-lightnx2**2))
lightnsim1 = normdpdx*lightnx1 + normdpdy*lightny1
lightnsim2 = normdpdx*lightnx2 + normdpdy*lightny2
if relief_type == 'concave':
    lightnsim1 *= -1
    lightnsim2 *= -1
lightnx = np.where(lightnsim1 <lightnsim2, lightnx2, lightnx1)
lightny = np.where(lightnsim1 <lightnsim2, lightny2, lightny1)
lightnz = np.where(lightnsim1 <lightnsim2, lightnz2, lightnz1)

# Calculate overall normal map
if cast_shadow:
    normalx = np.where(shadowmask==1,shadownx, lightnx)
    normaly = np.where(shadowmask==1,shadowny, lightny)
    normalz = np.where(shadowmask==1,shadownz, lightnz)
else:
    normalx = lightnx
    normaly = lightny
    normalz = lightnz

# Combine channels for export, the y-channel is reversed since numpy arrays have y axis pointing down
normalmap = np.dstack((normalx/2+0.5, normaly/-2+0.5, normalz/2+0.5))
imageio.imwrite(normaloutput,normalmap)

# Calculate displacement maps
displacex = np.where((normalz==0)|(abs(normalx/normalz)>displace_threshold),
                     -1*displace_threshold*normalx/abs(normalx), np.nan_to_num(-1*normalx/normalz))
displacey = np.where((normalz==0)|(abs(normaly/normalz)>displace_threshold),
                     -1*displace_threshold*normaly/abs(normaly), np.nan_to_num(-1*normaly/normalz))

# Calculate mipmap pyramid for discplacement maps
def mipmap(displacemap):
    pyramid = []
    base = displacemap
    pyramid.append((base[:,:], base.shape))
    while min(base.shape) > 1:
        base = scipy.ndimage.zoom(base,0.5)
        pyramid.append((base[:, :], base.shape))
    pyramid.reverse()
    return pyramid

# Smooth map
def smooth(map, threshold, factor):
    mask = np.where(sobelmag<threshold,1,0)
    imputed = sobelneighbors(map, sobelmag*-1, threshold*-1)
    smoothed = np.where(mask==0, imputed, map)
    smoothed = scipy.ndimage.gaussian_filter(smoothed, sigma=factor)
    smoothed = np.where(mask==0, map, smoothed)
    return smoothed

displacex = np.nan_to_num(smooth(displacex, smooth_threshold, smooth_factor))
displacey = np.nan_to_num(smooth(displacey, smooth_threshold, smooth_factor))

# Calculate Depthmap
def integrationrot(displacex, displacey, fold, negative = False):
    depthmap = np.zeros_like(displacex)
    for i in range(0, fold+1):
        angle = i*math.pi/2/(fold+1)
        if negative:
            angle *= -1
        diffmapx = np.nan_to_num(displacex*math.cos(angle)+displacey*math.cos(angle))
        diffmapy = np.nan_to_num(-1*displacex*math.sin(angle)+displacey*math.cos(angle))
        if angle != 0:
            diffmapx = rotate(diffmapx, angle)
            diffmapy = rotate(diffmapy, angle)
        depthmapi = np.nancumsum(diffmapx, axis=0) + np.nancumsum(diffmapy, axis=1)
        depthmapi[np.isnan(diffmapx)]=np.nan
        depthmap += rotate(depthmapi, -1*angle)
    return depthmap

def neighbors(image):
    blank = np.full((image.shape[0]+2, image.shape[1]+2),np.nan)
    center = np.copy(blank)
    center[1:-1,1:-1] = image
    top = np.copy(blank)
    top[:-2,1:-1] = image
    top[-2,:]=0
    bottom = np.copy(blank)
    bottom[2:,1:-1] = image
    bottom[1,:]=0
    left = np.copy(blank)
    left[1:-1,:-2] = image
    left[:,-2]=0
    right =np.copy(blank)
    right[1:-1,2:]=image
    right[:,1] = 0
    return center, left, right, top, bottom

def integrationpyr(displacex, displacey, initialiterations, finaliterations):
    fullx = displacex.shape[1]
    fully = displacex.shape[0]
    xpyramid = mipmap(displacex)
    ypyramid = mipmap(displacey)
    initial = None
    for i in range(len(xpyramid)):
        xneighbors = neighbors(xpyramid[i][0])
        yneighbors = neighbors(ypyramid[i][0])
        xfactor = fullx / xpyramid[i][1][1]
        yfactor = fully / xpyramid[i][1][0]
        if initial is None:
            initial = np.zeros(xpyramid[0][1])
            initialneighbors = neighbors(initial)
        if i != len(xpyramid)-1:
            iterations = initialiterations
        else:
            iterations = finaliterations
        for t in range(iterations):
            final=(sum(initialneighbors[1:])
                   +xfactor*(xneighbors[1]-xneighbors[2])+yfactor*(yneighbors[3]-yneighbors[4]))/4
            initial = final[1:-1,1:-1]
            initial[1:-1,(0,-1)] *= 4/3
            initial[(0,-1), 1:-1] *=4/3
            initial[(0,-1), (0,-1)] *=2
            initial[(0, -1), (-1, 0)] *= 2
            if t == iterations - 1 and i != len(xpyramid)-1:
                initial = resize(initial, xpyramid[i+1][0].shape)
            initialneighbors = neighbors(initial)
    return initial

if integration_algorithm == 'rotation':
    depthmap = integrationrot(displacex, displacey, integration_fold)
else:
    depthmap = integrationpyr(displacex, displacey, initial_iterations, final_iterations)

# Bias Correction
def biascorrect(depthmap, complexity = 'linear'):
    y = np.repeat(np.arange(0,depthmap.shape[0]),depthmap.shape[1])
    x = np.repeat(np.arange(0,depthmap.shape[1])[np.newaxis,:],depthmap.shape[0], axis=0).flatten()
    xy = x*y
    z = np.nan_to_num(depthmap.flatten())
    model = LinearRegression()
    if complexity == 'quadratic':
        y2 =y**2
        x2= x**2
        model.fit(np.array([x, y, xy, x2, y2]).T, z)
        bias = model.predict(np.array([x, y, xy, x2, y2]).T).reshape((depthmap.shape[0], depthmap.shape[1]))
    else:
        model.fit(np.array([x, y, xy]).T, z)
        bias = model.predict(np.array([x, y, xy]).T).reshape((depthmap.shape[0], depthmap.shape[1]))
    newdepthmap = depthmap - bias
    return newdepthmap


depthmap = biascorrect(depthmap, bias_complexity)
depthmap = smooth(depthmap, final_smooth_threshold, final_smooth_factor)
depthmap = smooth(depthmap, 10, full_smooth_factor)
depthmap = (depthmap - np.nanmin(depthmap))/(np.nanmax(depthmap)-np.nanmin(depthmap))
imageio.imwrite(depthoutput,depthmap)

# Display results
fig, ax = plt.subplots(2,4)
ax[0,0].imshow(image, cmap='gray', vmin=0, vmax=1)
ax[0,0].set_title('Image')
ax[0,1].hist(shadow[0], bins=[x/255 for x in range(256)], density = True, alpha = 0.5, label='shadow')
ax[0,1].hist(image.flatten(), bins=[x/255 for x in range(256)], density = True, alpha=0.5, label = 'total')
ax[0,1].set_title('Histogram')
ax[0,1].legend(['shadow','total'])
ax[0,2].imshow(shadowmask, cmap='gray', vmin=0, vmax=1)
ax[0,2].set_title('Shadow Mask')
ax[0,3].imshow(normalmap)
ax[0,3].set_title('Normal Map')
ax[1,0].plot(scantheta[0], scale(scantheta[1]),scantheta[0], normalize(1/normalize(scantheta[2])),scantheta[0],
             scale([-1*x for x in scantheta[3]]),scantheta[0], f(scantheta,0.5,1.5))
ax[1,0].legend(['SS from Mean','1/Partial Derivative','-SS from Adjacent','Desirability'])
ax[1,0].set_title('Angle Scanning Results')
ax[1,1].plot([a/100 for a in range(flat_width,101-flat_width)],flatvector)
ax[1,1].set_title('Maximum Continuous Value Range')
ax[1,2].imshow(displacex+displacey)
ax[1,2].set_title('Differential Displacement')
ax[1,3].imshow(depthmap, cmap='gray', vmin=0, vmax=1)
ax[1,3].set_title('Depth Map')
plt.show()

