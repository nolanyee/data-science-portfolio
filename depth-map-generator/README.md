# Depth Map Generator
*Skills: Python, Image Processing, Linear Algebra, Multivariable Calculus*

### Overview
This program generates a depth map from a monocular image of matte monochromatic bas-relief. The algorithm uses physical principles of light to calculate a normal map, which is integrated to a depth map. 

*Prerequisite Libraries: scipy, numpy, imageio, matplotlib, sklearn, skimage, tkinter*

### Motivation
When texturing 3D models, most of the time having only a diffuse channel is not enough. In architectural modeling specifically, it is quite noticeable when the texture of a relief carving consists of only a diffuse channel whose color is from a photograph of the carving. To achieve realistic surfaces without modeling the detail, a bump map (i.e. depth map) or normal map is required. However, it is often the case that there is no available depth map or normal map corresponding to the image. Therefore it is beneficial to have a program that can generate a normal map and depth map from the photograph itself. This program focuses on monochromatic images of bas-reliefs because it is primarily meant for architectural texturing purposes. Generating depth maps from color images is more difficult because it is hard to tell the difference between darker color and shadow, so such images are out of the scope of this project.

### Usage
The graphical user interface enables the user to set any of the parameters used in the depth map generation. 

<img src="images/ScreenShot.jpg" width ="500">

If nothing is changed the default settings will be used. The input image and output normal map and depth map image file names are mandatory. Once everything is filled out, press "OK" and the calculation will begin. When calculation is finished, the following window will appear and the files will have been saved.

<img src="images/Figure_1.png" width ="900">

The meaning of all the plots above are discussed in the sections below.

## Technical Details
### Light Scattering
The main assumption used to generate the depth map is that when incoming light hits the surface is scattered equally in all directions. This assumption holds true if the surface is the same color throughout and the surface is matte.

<img src="images/DepthMapFig1.png" width ="400">

If the assumption holds, then the intensity of scattered light reaching the observer is the same for all regions of the surface that have the same amount of incident light.

<img src="images/DepthMapFig2.png" width ="400">

However, depending on the angle of the light and the shape of the surface, some parts of the surface will have less incident light than other parts. The surface that is normal to the light direction will have the most incident light hitting it per area of the image (the projection of the surface onto the image plane). And the surface that is parallel to the light direction will have the least light. 

<img src="images/DepthMapFig3.png" width ="400">

The amount of incident light the surface recieves is proportional to the cosine of the light vector and the surface normal vector.


