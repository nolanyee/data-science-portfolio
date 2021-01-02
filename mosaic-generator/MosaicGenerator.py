'''
This program converts an image to a mosaic. The output is an image (diffuse), depth map, normal map, and specular map.
The algorithm builds upon the work of A. Hausner. Simulating Decorative Mosaics. SIGGRAPH'01: 573-580, 2001.
'''

import scipy.ndimage
import scipy.stats
import scipy.misc
import math
import imageio
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches
import matplotlib.collections
from skimage.transform import resize
from tkinter import *
from tkinter.ttk import *
import random
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg

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

headinglabel1 = Label(frame, text='FILE PATHS')
headinglabel1.grid(row=1, column=0, sticky=E)

parameterfield('InputFile','  Input File Name (including path)',80,'',2)
parameterfield('OutputPath','Output Folder Path',80,'',3)

headinglabel2 = Label(frame, text='GRADIENT CALCULATION')
headinglabel2.grid(row=4, column=0, sticky=E)

parameterfield('GradientRadius','Gradient Measurement Distance',5,7,5)
parameterfield('SobelWt','Sobel Weight',5,1,6)
parameterfield('ConnectDist','Connectivity Distance',5,5,7)
parameterfield('ExclusionLower','Exclusion Lower Threshold',5,0.2,8)
parameterfield('ConeUpper','Cone Upper Percentile',5,0.95,9)
parameterfield('ConeLower','Cone Lower Percentile',5,0.90,10)
parameterfield('SmoothingRadius','Smoothing Radius',5,3,11)

headinglabel3 = Label(frame, text='VORONOI DIAGRAM')
headinglabel3.grid(row=12, column=0, sticky=E)

parameterfield('EdgePercentile','Edge Mask Percentile',5,0.90,13)
parameterfield('EdgePenalty','Edge Penalty',5,0.5,14)
parameterfield('Beta','Aspect Ratio Factor',5,1.5,15)
parameterfield('TileNumber','Number of Tiles',5,1000,16)
parameterfield('VoronoiIterations','Voronoi Iterations',5,20,17)

headinglabel4 = Label(frame, text='TILE SHAPE ADJUSTMENT')
headinglabel4.grid(row=18, column=0, sticky=E)

parameterfield('Delta','Tile Shrinkage Parameter',5,0.8,19)
parameterfield('Increment','Tile Adjustment Increment',5,4,20)
parameterfield('TileIterations','Tile Adjustment Iterations',5,5,21)
parameterfield('DilationNumber','Dilation Radius',5,50,22)
parameterfield('ErosionNumber','Erosion Radius',5,'',23)

headinglabel5 = Label(frame, text='TEXTURE GENERATION')
headinglabel5.grid(row=24, column=0, sticky=E)

parameterfield('Scale','Output Scale Factor',5,2.0,25)
parameterfield('TiltAngle','Maximum Tilt Angle',5,10,26)
parameterfield('TileDepth','Maximum Tile Depth',5,0.5,27)
parameterfield('GroutDepth','Grout Depth',5,1,28)
parameterfield('NormalDepth','Normal Map Depth Factor',5,1,29)
parameterfield('GroutColor','Grout Color',10,'#333333',30)

def done():
    global loopactive
    window.update_idletasks()
    window.withdraw()
    loopactive = False

okbutton =Button(frame, text='OK', command=done)

okbutton.grid(row=31, column = 1, sticky = W)

while loopactive:
    window.update()

# PARAMETER SETTING

InputFile = InputFileentry.get()
OutputPath = OutputPathentry.get()
GradientRadius = int(GradientRadiusentry.get()) # Number of pixels on each side for measuring gradient
SobelWt = float(SobelWtentry.get()) # Weight of Sobel Filter relative to custom gradient calculation
ConnectDist = int(ConnectDistentry.get()) # Number of pixels used to average neighbors for noise reduction
ExclusionLower = float(ExclusionLowerentry.get()) # Fraction of range of gradient, below which gradient is set to 0
ConeUpper = float(ConeUpperentry.get()) # Upper percentile of gradient intensity, which more intense values are set to
ConeLower = float(ConeLowerentry.get()) # Lower percentile of gradient intensity, above which cones are calculated
SmoothingRadius = int(SmoothingRadiusentry.get()) # Gaussian filter radius in pixels
EdgePercentile = float(EdgePercentileentry.get()) # Percentile of gradient intensity required for edge mask
EdgePenalty = float(EdgePenaltyentry.get()) # Penalty used to weight edge pixels in centroid determination
Beta = float(Betaentry.get()) # Aspect Ratio factor, amount tiles are stretched parallel to edges at edges (1 = square)
TileNumber = int(TileNumberentry.get()) # Number of tiles
VoronoiIterations = int(VoronoiIterationsentry.get()) # Number of iterations of Lloyd's algorithm
Delta = float(Deltaentry.get()) # Tile dilation factor (recommend 0.8), smaller values reduce tile overlap
Increment = float(Incremententry.get()) # Amount tile corners are moved in each iteration (recommend 1 to start)
TileIterations = int(TileIterationsentry.get()) # Number of iterations for tile adjustment algorithm (gradient descent)
DilationNumber = int(DilationNumberentry.get()) # Pixels to dilate the tiles in generation of tile gradient
if ErosionNumberentry.get() is None or ErosionNumberentry.get() == '' or ErosionNumberentry.get() == 'None':
    ErosionNumber = None
else:
    ErosionNumber = int(ErosionNumberentry.get()) # Pixels to erode the tiles in generation of tile gradient
Scale = float(Scaleentry.get())/100 # Resolution is increased by the scale factor (since dpi = 100)
TiltAngle = float(TiltAngleentry.get()) # Maximum angle (degrees) for tiles to be randomly tilted from flat
TileDepth = float(TileDepthentry.get()) # Maximum depth for tiles to be randomly sunken, relative to tile size
GroutDepth = float(GroutDepthentry.get()) # Depth of grout, relative to depth range of tile surfaces
NormalDepth = float(NormalDepthentry.get()) # Factor to increase slopes of depth map before generating normal map
GroutColor = GroutColorentry.get() # Grout color, may be hex, RBG tuple, or matplotlib named color

window.destroy()
# IMAGE PROCESSING

# Reading input file
image = imageio.imread(InputFile)
shape0 = image.shape[0]
shape1 = image.shape[1]

# Custom Gradient calculation from neighboring pixels
def gradient(r=1):
    calcMatrix= np.full(((2*r+1)**2, shape0+2*r, shape1+2*r, 8),np.nan)
    calcMatrix[(2*r+1)**2//2, r:shape0+r, r:shape1+r, :3] = image
    centralImage = calcMatrix[(2*r+1)**2//2,:,:,:]
    maskMatrix = np.full(((2*r+1)**2, 6), 0)
    for i in range((2*r+1)**2):
        calcMatrix[i, i//(2*r+1):shape0+i//(2*r+1), i%(2*r+1):shape1+i%(2*r+1), :3] = image
        if math.sqrt((i//(2*r+1)-r)**2 + (i%(2*r+1)-r)**2) != 0:
            calcMatrix[i, :, :, 3] = abs(i//(2*r+1)-r)/math.sqrt((i//(2*r+1)-r)**2 + (i%(2*r+1)-r)**2)
            calcMatrix[i, :, :, 4] = abs(i%(2*r+1)-r)/math.sqrt((i//(2*r+1)-r)**2 + (i%(2*r+1)-r)**2)
        else:
            calcMatrix[i, :, :, 3] = 0
            calcMatrix[i, :, :, 4] = 0
        diff = np.sqrt(np.nansum(np.square(calcMatrix[i,:,:,:3]-centralImage[:,:,:3]),2))*np.sign(np.nansum(calcMatrix[i,:,:,:3]-centralImage[:,:,:3],2))
        calcMatrix[i, :, :, 5] = diff*calcMatrix[i, :, :, 3]
        calcMatrix[i, :, :, 6] = diff*calcMatrix[i, :, :, 4]
        calcMatrix[i, :, :, 7] = diff
        if i//(2*r+1) < r:
            maskMatrix[i,0]=1
        if i//(2*r+1) > r:
            maskMatrix[i,1]=1
        if i%(2*r+1) < r:
            maskMatrix[i,2]=1
        if i%(2*r+1) > r:
            maskMatrix[i,3]=1
        if (i//(2*r+1) < r and i%(2*r+1) < r) or (i//(2*r+1) > r and i%(2*r+1) > r):
            maskMatrix[i,4]=1
        if (i//(2*r+1) < r and i%(2*r+1) > r) or (i//(2*r+1) > r and i%(2*r+1) < r):
            maskMatrix[i,5]=1
    SignMatrix = np.where(np.abs(np.nanmean(calcMatrix[:,:,:,7]*maskMatrix[:,4].reshape(-1,1,1),0))-np.abs(np.nanmean(calcMatrix[:,:,:,7]*maskMatrix[:,5].reshape(-1,1,1),0)) >=0, 1, -1)
    YMatrix = np.abs(np.nanmean(calcMatrix[:,:,:,5]*maskMatrix[:,0].reshape(-1,1,1),0))+np.abs(np.nanmean(calcMatrix[:,:,:,5]*maskMatrix[:,1].reshape(-1,1,1),0))
    XMatrix =SignMatrix*(np.abs(np.nanmean(calcMatrix[:,:,:,6]*maskMatrix[:,2].reshape(-1,1,1),0))+np.abs(np.nanmean(calcMatrix[:,:,:,6]*maskMatrix[:,3].reshape(-1,1,1),0)))
    return XMatrix[r:shape0+r, r:shape1+r], YMatrix[r:shape0+r, r:shape1+r], np.sqrt(XMatrix[r:shape0+r, r:shape1+r]**2, YMatrix[r:shape0+r, r:shape1+r]**2)

# Generation of a larger cone image, which is sliced to generate cones for each edge pixel
def cone():
    Coords0 =np.repeat([np.arange(0,shape0*2+1)],shape1*2+1,0).T
    Coords1 = np.repeat([np.arange(0,shape1*2+1)],shape0*2+1,0)
    coneMatrix= 1-np.sqrt((shape0-Coords0)**2+(shape1-Coords1)**2)/max(1,math.sqrt(shape0**2+shape1**2))
    return coneMatrix

coneMatrix = cone()

# Slicing of larger cone image based on edge pixel position
def pixelCone(index0, index1):
    return coneMatrix[shape0-index0:2*shape0-index0, shape1-index1:2*shape1-index1]

# Normalizing gradient map
def normalize(gradient, upperLimit =1):
    return np.minimum((gradient-np.nanmin(gradient))/(np.nanmax(gradient)-np.nanmin(gradient)),upperLimit)

# Generation of orientation map by superimposing cones of edge pixels and taking maximum value
def ridgeCalc(gradient, upperLimit =0.98, lowerLimit =0.95):
    initialNormalized = np.nan_to_num(normalize(gradient,1))
    normGradient = normalize(gradient, np.percentile(initialNormalized,upperLimit*100))
    ridgeMask = np.where(normGradient >= np.percentile(initialNormalized,lowerLimit*100), 1.0, np.NaN)
    Coords0 =np.repeat([np.arange(0,shape0)],shape1,0).T*ridgeMask
    Coords1 = np.repeat([np.arange(0,shape1)],shape0,0)*ridgeMask
    Coords0 = Coords0[~np.isnan(Coords0)].astype(int)
    Coords1 = Coords1[~np.isnan(Coords1)].astype(int)
    coneNumber = int(np.nansum(ridgeMask))
    individualCones = np.full((shape0, shape1),np.NaN)
    for i in range(coneNumber):
        individualCones = np.nanmax([individualCones, pixelCone(Coords0[i], Coords1[i])+normGradient[Coords0[i], Coords1[i]]],0)
    return individualCones

# Sobel magnitude
def sobel():
    return np.sqrt(scipy.ndimage.sobel(np.sum(image,2),0)**2+scipy.ndimage.sobel(np.sum(image,2),1)**2)

# Uniform filter is applied to penalize edge pixels that aren't connected to others
def connected(gradient, lowerLimit =0.25, n=10):
    initialNormalized = np.nan_to_num(normalize(scipy.ndimage.uniform_filter(gradient,n),1))
    normGradient = normalize(gradient, np.percentile(initialNormalized,100))
    return np.where(normGradient>=lowerLimit, gradient*normGradient, 0)

# Linear combination of custom gradient map and sobel map
def mixedConnected(meanGradient, sobelGradient, r, sobelWt=1.0, lowerLimit =0.25, n=10):
    return connected(meanGradient/sobelWt + sobelGradient*sobelWt/r, lowerLimit, n)

# Calculating gradient map

imgGradient = gradient(GradientRadius)[2]

imgSobel = sobel()

mixedGradient = mixedConnected(imgGradient, imgSobel, GradientRadius, SobelWt, ExclusionLower,ConnectDist)

# Edge mask is a binary map of edge pixels above a specified percentile
edgeMask = np.where(mixedGradient>np.percentile(mixedGradient,EdgePercentile*100),1,0)

# Calculation of orientation map
orientImage = ridgeCalc(mixedGradient,ConeUpper,ConeLower)

orientImageSmoothed = scipy.ndimage.gaussian_filter(orientImage,SmoothingRadius)

orientImageNorm = (orientImageSmoothed-np.nanmin(orientImageSmoothed))/(
        np.nanmax(orientImageSmoothed)-np.nanmin(orientImageSmoothed))

orient0 = scipy.ndimage.sobel(orientImageSmoothed,0)
orient1 = scipy.ndimage.sobel(orientImageSmoothed,1)
orient0norm = orient0/np.sqrt(orient0**2+orient1**2)
orient1norm = orient1/np.sqrt(orient0**2+orient1**2)

# Lloyd's algorithm using oriented rectangular pyramids instead of cones
def voronoi(beta = 1.0, penalty = 0.0, n=50, inputDiagram = None):
    x0 = np.repeat([np.arange(0,shape0)],shape1,0).T
    x1 = np.repeat([np.arange(0,shape1)],shape0,0)
    if inputDiagram is None:
        blockArea = (shape0*shape1)/n
        blockLength = math.sqrt(blockArea)
        dim0 = shape0//blockLength
        dim1 = shape1//blockLength
        blockLength0 = shape0/dim0
        blockLength1 = shape1/dim1
        centroids = []
        for i in range(int(dim0)):
            for j in range(int(dim1)):
                centroids.append([int(round((i+0.5)*blockLength0,0)),int(round((j+0.5)*blockLength1,0))])
    else:
        inputLabels = inputDiagram[:,:,1]
        regionCount = np.nanmax(inputLabels)
        centroids = []
        for i in range(regionCount):
            try:
                denominators = np.nansum(np.where(inputLabels == i, (1-edgeMask*penalty), np.NaN))
                centroids.append([int(round(np.nansum(np.where(inputLabels == i, x0*(1-edgeMask*penalty), np.NaN))/denominators,0)), int(round(np.nansum(np.where(inputLabels == i, x1*(1-edgeMask*penalty), np.NaN))/denominators,0))])
            except:
                pass
    diagram = np.full((shape0,shape1,2),0)
    diagram[:,:,0] = max(beta, 1/beta)*(shape0+shape1)
    layer = np.full((shape0,shape1,2),np.NaN)
    for i in range(len(centroids)):
        c0 = centroids[i][0]
        c1 = centroids[i][1]
        u0 = orient0norm[c0,c1]
        u1 = orient1norm[c0,c1]
        effectiveBeta = (beta-1)*orientImageNorm[c0,c1]+1
        layer[:,:,0] = np.maximum(effectiveBeta*np.abs((x0-c0)*u0+(x1-c1)*u1),(1/effectiveBeta)*np.abs((x1-c1)*u0-(x0-c0)*u1))
        layer[:,:,1] = i
        diagram[:,:,1] = np.where(layer[:,:,0] < diagram[:,:,0],i,diagram[:,:,1])
        diagram[:,:,0] = np.minimum(diagram[:,:,0],layer[:,:,0])
    return diagram

def iterativeVoronoi(iterations = 1, beta = 1.0, penalty = 0.0, n=50):
    inputDiagram = None
    for i in range(iterations):
        inputDiagram = voronoi(beta, penalty, n, inputDiagram)
    return inputDiagram

# Calculating Voronoi diagram
finalVoronois = iterativeVoronoi(VoronoiIterations,Beta,EdgePenalty,TileNumber)
finalVoronoi = finalVoronois[:,:,1]

# Coloring Voronoi Diagram with mean of colors in each region
def colorVoronoi():
    tileCount = np.nanmax(finalVoronoi)+1
    crystallized = image
    colorVoronoi = finalVoronoi.reshape(shape0,shape1,1)
    for i in range(tileCount):
        color = np.nanmean(np.where(colorVoronoi == i, 1,np.NaN)*crystallized,(0,1)).astype(int)
        crystallized = np.where(colorVoronoi == i, color,crystallized)
    return crystallized

# Generation of a binary matrix approximating a circular mask
def radial(r):
    x1 = np.repeat([np.arange(0,2*r+1)],2*r+1,0)
    x0 = x1.T
    matrix = np.where(np.sqrt((x0-r)**2+(x1-r)**2)<=r+1,1,0)
    matrix = matrix/np.sum(matrix)
    return matrix

# Creation of superimposed pyramid for all tiles
def coneStroke(image, R):
    newImage = image
    for i in range(1, R+1):
        newImage = np.maximum(scipy.ndimage.binary_dilation(image, radial(i))*(1-i/(R+1)), newImage)
    return newImage

# Creating polygons from centroid position, orientation map, and shape parameters
def polygons(beta=1.0, delta = 0.8):
    N = np.nanmax(finalVoronoi)
    x0 = np.repeat([np.arange(0,shape0)],shape1,0).T
    x1 = np.repeat([np.arange(0,shape1)],shape0,0)
    dim = delta*math.sqrt(shape0*shape1/N)
    halfdim = dim/2
    polygons = []
    pointArray = []
    for i in range(1,N+1):
        c0 = np.nanmean(np.where(finalVoronoi == i, x0, np.NaN))
        c1 = np.nanmean(np.where(finalVoronoi == i, x1, np.NaN))
        c0Int =int(round(c0))
        c1Int =int(round(c1))
        u0 = orient0norm[c0Int,c1Int]
        u1 = orient1norm[c0Int,c1Int]
        effectiveBeta = (beta-1)*orientImageNorm[c0Int,c1Int]+1
        points = [[c1+u1*halfdim/effectiveBeta+u0*halfdim*effectiveBeta, shape0-(c0+u0*halfdim/effectiveBeta-u1*halfdim*effectiveBeta)],
                  [c1+u1*halfdim/effectiveBeta-u0*halfdim*effectiveBeta, shape0-(c0+u0*halfdim/effectiveBeta+u1*halfdim*effectiveBeta)],
                  [c1-u1*halfdim/effectiveBeta-u0*halfdim*effectiveBeta, shape0-(c0-u0*halfdim/effectiveBeta+u1*halfdim*effectiveBeta)],
                  [c1-u1*halfdim/effectiveBeta+u0*halfdim*effectiveBeta, shape0-(c0-u0*halfdim/effectiveBeta-u1*halfdim*effectiveBeta)]]
        polygoni = matplotlib.patches.Polygon(points, closed=True, fill = True, color = "w")
        polygons.append(polygoni)
        pointArray.append(points)
    return polygons, pointArray

# Calculate polygons
tesserae = polygons(Beta,Delta)

# Render polygons using matplotlib, and convert output back into numpy matrix
def renderPolygons(polylist, scale = 0.05, close=True):
    fig = Figure(figsize=(shape1*scale,shape0*scale),frameon=False)
    canvas = FigureCanvasAgg(fig)
    ax = fig.subplots()
    p = matplotlib.collections.PatchCollection(polylist, facecolors = 'w')
    ax.add_collection(p)
    ax.set_xlim([0,shape1])
    ax.set_ylim([0,shape0])
    ax.set_facecolor('k')
    ax.axes.get_xaxis().set_visible(False)
    ax.axes.get_yaxis().set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    fig.tight_layout(pad=0)
    canvas.draw()
    rows, cols = canvas.get_width_height()
    newimage = np.frombuffer(canvas.tostring_rgb(), dtype=np.uint8).reshape(cols, rows, 3)[:,:,0]
    newimage = np.round(newimage/255,0)
    if close:
        plt.close()
    return newimage

# Adjust corners of polygon using iterative gradient decent, re-calculating gradient after each iteration
def adjustCorners(polylist, increment = 1.0, outerN=50, innerN=None, scale=0.05):
    if innerN is None:
        innerN = int(round(2*math.sqrt(shape0*shape1/len(polylist[1])),0))
    raster = renderPolygons(polylist[0], scale)
    peaks = 1-coneStroke(1-raster,innerN)+coneStroke(raster,outerN)
    peaks = 1-(peaks-np.nanmin(peaks))/(np.nanmax(peaks)-np.nanmin(peaks))
    grad0 = scipy.ndimage.sobel(peaks,0)
    grad1 = scipy.ndimage.sobel(peaks,1)
    peaksize0 = peaks.shape[0]
    peaksize1 = peaks.shape[1]
    gradScale = peaks.shape[0]/shape0
    newpolylist = polylist[1]
    newpolygons = []
    for i in range(len(polylist[1])):
        for j in range(4):
            coord0 = (shape0-polylist[1][i][j][1])*gradScale
            coord1 = polylist[1][i][j][0]*gradScale
            coord0Int = int(round(coord0,0))
            coord1Int = int(round(coord1,0))
            if coord0Int <0 or coord1Int <0 or coord0Int >= peaksize0 or coord1Int >= peaksize1:
                newCoord0 = coord0
                newCoord1 = coord1
            else:
                newCoord0 = coord0+grad0[coord0Int, coord1Int]*increment*scale*72
                newCoord1 = coord1+grad1[coord0Int, coord1Int]*increment*scale*72
            newpolylist[i][j][0]= newCoord1/gradScale
            newpolylist[i][j][1]= shape0-newCoord0/gradScale
        polygoni = matplotlib.patches.Polygon(newpolylist[i], closed=True, fill = True, color = "w")
        newpolygons.append(polygoni)
    return newpolygons, newpolylist

def iterateCorners(polylist, iterations, increment = 1.0, outerN=50, innerN=None, scale=0.05):
    currentTesserae = polylist
    for i in range(iterations):
        currentTesserae = adjustCorners(currentTesserae, increment, outerN, innerN, scale)
    return currentTesserae

# Adjust corners of tiles
adjustedTesserae = iterateCorners(tesserae, TileIterations, Increment, DilationNumber, ErosionNumber, Scale)

# Create list of colors corresponding to each tile by taking the mean in each tile region
def colorTesserae(polylist):
    tileCount = len(polylist[1])
    crystallized = image
    colorMosaic = np.full((shape0,shape1,3),0)
    colors = []
    for i in range(tileCount):
        tile = resize(renderPolygons(adjustedTesserae[0][i:i+1]),(shape0,shape1,1))
        color = np.nanmean(np.where(tile>0, 1,np.NaN)*crystallized,(0,1)).astype(int)
        colorMosaic = np.where(tile>0, color,colorMosaic)
        colors.append(tuple(color))
    return colorMosaic, colors

colors = colorTesserae(adjustedTesserae)

# Render tiles with color list
def renderPolygonsColor(polylist, colorlist, scale = 0.05, grout = 'k', close=True):
    fig = Figure(figsize=(shape1 * scale, shape0 * scale), frameon=False)
    canvas = FigureCanvasAgg(fig)
    ax = fig.subplots()
    p = matplotlib.collections.PatchCollection(polylist, facecolors = 'w')
    p.set_facecolors(np.maximum(np.array(colorlist),0)/255)
    ax.add_collection(p)
    ax.set_xlim([0,shape1])
    ax.set_ylim([0,shape0])
    ax.set_facecolor(grout)
    ax.axes.get_xaxis().set_visible(False)
    ax.axes.get_yaxis().set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    fig.tight_layout(pad=0)
    fig.canvas.draw()
    canvas.draw()
    rows, cols = canvas.get_width_height()
    newimage = np.frombuffer(canvas.tostring_rgb(), dtype=np.uint8).reshape(cols, rows, 3)
    if close:
        plt.close()
    return newimage

# Generate depth map and normal maps
def gradientTesserae(polylist, tilt = 10.0, position = 0.5, drop=1.0, normalstretch=1.0, scale=0.05):
    render = renderPolygons(adjustedTesserae[0],scale,True)
    render0 = render.shape[0]
    render1 = render.shape[1]
    tileCount = len(polylist[1])
    colorMosaic = np.full((render0,render1),np.NaN)
    renderEdge0 = scipy.ndimage.sobel(render,0)
    renderEdge1 = scipy.ndimage.sobel(render,1)
    renderEdgeMask = np.where((renderEdge0 == 0)&(renderEdge1 == 0),1,0)
    normalMapFront = np.full((render0, render1, 3), np.NaN)
    normalMapBack = np.full((render0, render1, 3), np.NaN)
    v0 = np.repeat([np.arange(0,render0)],render1,0).T
    v1 = np.repeat([np.arange(0,render1)],render0,0)
    for i in range(tileCount):
        tile = renderPolygons(adjustedTesserae[0][i:i+1], scale, True)
        tilemin0 = render0-np.nanargmax(np.nansum(np.nancumsum(np.flip(tile,0), 0),1))
        tilemax0 = np.nanargmax(np.nansum(np.nancumsum(tile, 0),1))
        tilemin1 = render1-np.nanargmax(np.nansum(np.nancumsum(np.flip(tile,1), 1),0))
        tilemax1 = np.nanargmax(np.nansum(np.nancumsum(tile, 1),0))
        angle = random.random()*2*math.pi
        height = random.random()*position*max((tilemax0-tilemin0),(tilemax1-tilemin1))
        tiltAngle = random.random()*2*math.pi*tilt/360
        y = math.sin(angle)*math.sin(tiltAngle)
        x = math.cos(angle)*math.sin(tiltAngle)
        z = math.cos(tiltAngle)
        z0 = (1-height)-abs((y*(tilemax0-tilemin0) + x*(tilemax1-tilemin1))/(2*z))
        x0 = (tilemin1+tilemax1)/2
        y0 = (tilemin0+tilemax0)/2
        color = z0 - ((x*(v1-x0)+y*(v0-y0))/z)
        colorMosaic = np.where(tile>0, color,colorMosaic)
        normalMapFront[:,:,0] = np.where((tile>0)&(renderEdgeMask>0), x, normalMapFront[:,:,0])
        normalMapFront[:,:,1] = np.where((tile>0)&(renderEdgeMask>0), y, normalMapFront[:,:,1])
        normalMapFront[:,:,2] = np.where((tile>0)&(renderEdgeMask>0), z, normalMapFront[:,:,2])
    tileRange = np.nanmax(colorMosaic)-np.nanmin(colorMosaic)
    colorMosaic = np.where(colorMosaic!=colorMosaic, np.nanmin(colorMosaic)-tileRange*drop, colorMosaic)
    sobely = scipy.ndimage.sobel(colorMosaic,0)/8
    sobelx = scipy.ndimage.sobel(colorMosaic,1)/8
    sobelmagnitude = np.sqrt(sobelx**2+sobely**2+1)
    normalMapBack[:,:,0]= np.where(normalMapFront[:,:,0] != normalMapFront[:,:,0], -1*sobelx/sobelmagnitude, normalMapFront[:,:,0])
    normalMapBack[:,:,1]= np.where(normalMapFront[:,:,1] != normalMapFront[:,:,1], -1*sobely/sobelmagnitude, normalMapFront[:,:,1])
    normalMapBack[:,:,2]= np.where(normalMapFront[:,:,2] != normalMapFront[:,:,2], 1/sobelmagnitude, normalMapFront[:,:,2])/normalstretch
    normalmagnitude = np.sqrt(normalMapBack[:,:,0]**2+normalMapBack[:,:,1]**2+normalMapBack[:,:,2]**2)
    normalMapBack[:,:,0] = normalMapBack[:,:,0]/normalmagnitude/2+0.5
    normalMapBack[:,:,1] = -1*normalMapBack[:,:,1]/normalmagnitude/2+0.5
    normalMapBack[:,:,2] = normalMapBack[:,:,2]/normalmagnitude/2+0.5
    normalMap = np.dstack((normalMapBack[:,:,0],normalMapBack[:,:,1],normalMapBack[:,:,2]))
    depthMap = (colorMosaic-np.nanmin(colorMosaic))/(np.nanmax(colorMosaic)-np.nanmin(colorMosaic))
    return depthMap, normalMap

# Generate Maps
maps = gradientTesserae(adjustedTesserae, TiltAngle, TileDepth, GroutDepth, NormalDepth, Scale)
diffuse =  renderPolygonsColor(adjustedTesserae[0],colors[1], Scale, GroutColor)
specular = renderPolygons(adjustedTesserae[0], scale= Scale)

# Export Maps
imageio.imwrite(OutputPath +'/MosaicDiffuse.png',diffuse)
imageio.imwrite(OutputPath +'/MosaicSpecular.png',np.round(specular*255).astype(np.uint8))
imageio.imwrite(OutputPath +'/MosaicDepth.png',np.round(maps[0]*255).astype(np.uint8))
imageio.imwrite(OutputPath +'/MosaicNormal.png',np.round(maps[1]*255).astype(np.uint8))

# Display results
fig, ax = plt.subplots(3,4, figsize=(12,9))
ax[0,0].imshow(image)
ax[0,0].set_title('Image')
ax[0,1].imshow(imgGradient)
ax[0,1].set_title('Custom Gradient')
ax[0,2].imshow(imgSobel)
ax[0,2].set_title('Sobel Gradient')
ax[0,3].imshow(mixedGradient)
ax[0,3].set_title('Mixed Gradient')
ax[1,0].imshow(edgeMask, cmap='gray')
ax[1,0].set_title('Edge Mask')
ax[1,1].imshow(orientImage)
ax[1,1].set_title('Orientation Map')
ax[1,2].imshow(orientImageSmoothed)
ax[1,2].set_title('Smoothed Orientation')
ax[1,3].imshow(orient0norm)
ax[1,3].set_title('Normalized Orientation')
ax[2,0].imshow(specular, cmap='gray')
ax[2,0].set_title('Specular Map')
ax[2,1].imshow(maps[0], cmap='gray')
ax[2,1].set_title('Depth Map')
ax[2,2].imshow(maps[1])
ax[2,2].set_title('Normal Map')
ax[2,3].imshow(diffuse)
ax[2,3].set_title('Diffuse Map')
plt.show()


