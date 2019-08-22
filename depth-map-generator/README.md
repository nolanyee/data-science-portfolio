# Depth Map Generator
*Skills: Python, Image Processing, Linear Algebra, Multivariable Calculus*

### Overview
This program generates a depth map from a monocular image of matte monochromatic bas-relief. The algorithm uses physical principles of light to calculate a normal map, which is integrated to a depth map. 

*Prerequisite Libraries: scipy, numpy, imageio, matplotlib, sklearn, skimage, tkinter*

### Motivation
When texturing 3D models, most of the time having only a diffuse channel is not enough. In architectural modeling specifically, it is quite noticeable when the texture of a relief carving consists of only a diffuse channel whose color is from a photograph of the carving. To achieve realistic surfaces without modeling the detail, a bump map (i.e. depth map) or normal map is required. However, it is often the case that there is no available depth map or normal map corresponding to the image. Therefore it is beneficial to have a program that can generate a normal map and depth map from the photograph itself. This program focuses on monochromatic images of bas-reliefs because it is primarily meant for architectural texturing purposes. Generating depth maps from color images is more difficult because it is hard to tell the difference between darker color and shadow, so such images are out of the scope of this project. However, they can be analyzed if the image is first normalized with a user defined color map before inputting into the program.

### Usage
The graphical user interface enables the user to set any of the parameters used in the depth map generation. 

<img src="images/ScreenShot.jpg" width ="500">

If nothing is changed the default settings will be used. The input image and output normal map and depth map image file names are mandatory. Once everything is filled out, press "OK" and the calculation will begin. When calculation is finished, the following window will appear and the files will have been saved.

<img src="images/Figure_1.png" width ="900">

The meaning of all the plots above are discussed in the sections below.

## Technical Details
### Diffuse Reflection
The main assumption used to generate the depth map is that when incoming light hits the surface is scattered equally in all directions. This kind of diffuse reflection or scattering is called Lambertian reflectance. This assumption holds true if the surface is the same color throughout and the surface is matte.

<img src="images/DepthMapFig1.png" width ="400">

If the assumption holds, then the intensity of scattered light reaching the observer is the same for all regions of the surface that have the same amount of incident light. Thus the intensity observed is proportionally to the intensity of incident light.

<img src="images/DepthMapFig2.png" width ="400">

However, depending on the angle of the light and the shape of the surface, some parts of the surface will have less incident light than other parts. The surface that is normal to the light direction will have the most incident light hitting it per area of the image (the projection of the surface onto the image plane). And the surface that is parallel to the light direction will have the least light. 

<img src="images/DepthMapFig3.png" width ="400">

The amount of incident light the surface recieves (and thus the amount of scattered light observed) is proportional to the cosine of the negative light vector and the surface normal vector, which is calculated by taking the dot product of the normalized vectors. However, when this cosine is negative the surface is in cast shadow (there cannot be negative light).

<img src="images/DepthMapFig4.png" width ="600">

A practical example of these principles is how sunlight hits the earth. During the night the observer is in cast shadow. During the day, the amount of sunlight (assuming no clouds) is related to latitude. During the summer there is more incident light because the angle between the light rays and the normal vector of the earth at that particular location (depends on lattitude) is smallest. And in winter it is the largest. The tropic of cancer recieves the most mid-day light during the summer because the normal vector of the earth is the same direction as the light vector.

### Reflected Light
In most images, regions with cast shadow are not completely black because of other light sources. The first possible source of light is light that is scattered from other parts of the surface. Light reflected from raised parts of the surface will be the most direct where the vector from the origin of the light to the location it strikes in the cast shadow is parallel to the surface normal of the shadow region. Overall, unless the other parts of the surface are much taller than the region of cast shadow, the reflected light will be generally strongest in the horizontal direction.

<img src="images/DepthMapFig5.png" width ="700">

This can also be seen applying the Huygens-Fresnel principle. The overall wavefront is moving roughly horizontally.

<img src="images/DepthMapFig7.png" width ="700">

Reflected light from flat areas of the surface are strongest in the areas of shadow where the surface is vertical and the normal is the horizontal, in the same direction as the reflected light source. This also leads to a strong horizontally directed light in the region of cast shadow.

<img src="images/DepthMapFig6.png" width ="700">

Once again this can also be seen applying Huygens-Fresnel principle.

<img src="images/DepthMapFig8.png" width ="700">

So overall, reflected light from the surface should be directed approximately horizontally in the direction opposite to the incident light. 

Reflected light can only come from areas that recieve incident light. Therefore no reflected light can come from the areas of cast shadow, which is in the direction of the incident light. Therefore on average the reflected light is directed roughly in the opposite direction of the incident light, when projected on the image plane.

<img src="images/DepthMapFig15.png" width ="500">

Therefore the reflected light vector is considered to be the negative projection of the incident light vector on the image plane (xy).

### Ambient Light
The second possible source of light in regions of cast shadow is ambient light. This is light coming from the environment. Ambient light can be the same intensity in all directions. In this case surfaces parallel to the image plane recieve more light than surfaces perpendicular to the image plane.

<img src="images/DepthMapFig9.png" width ="700">

This situation can be approximated as a light source pointing in the same direction as the normal of the image plane (in the z direction).

Alternatively, the light source can be from a distant surface that has diffuse reflection. For example if the relief is displayed vertically, the scattered light from the opposite wall would hit the surface. If the relief is displayed horizontally, the scattered light would be from the ceiling. In either case using the Huygens-Fresnel principle this light would be equivalent to light pointing in the z direction, making it the same as the previous case.

<img src="images/DepthMapFig10.png" width ="700">

### Additional Approximations
As a simplification, only diffuse reflectance will be considered in areas recieving incident light. And either reflected light or ambient light will be considered in the calculations for regions of cast shadow (the user must select which type of light is predominant).

However, all the theory discussed above still does not give enough information to decude the surface normal vector. It only gives the angle between the normal vector and the light vector. But this still forms a cone with an infinite number of possible normal vectors.

<img src="images/DepthMapFig11.png" width ="200">

Another major assumption is needed to determine which vector it is. The assumption will be that the contours of the image intensity function (the image itself) and the contours of the actual surface are the same. This means the projection of the normal vector onto the image (xy) plane is parallel to the gradient of the image intensity function (this gradient is estimated using a Sobel filter). Note that the gradient direction is sometimes ambiguous as to whether the normal should be pointing in the same direction or opposite direction (whether the cosine should target 1 or -1). By default the algorithm will target 1. This is called the "convexity" assumption. If the user chooses "concave" in the type of relief, the program will target -1.

There may be instances where the direction of the gradient of the image is not included in the projection of all possible normal vectors onto the xy plane. In this case the vector that is most similar (in terms of cosine) to the gradient vector is chosen (again targeting 1 if "convex", and -1 if "concave").

<img src="images/DepthMapFig16.png" width ="300">

This normal vector will end up always being one of two extreme normals. Therefore the two extreme normal vectors (the ones that have the largest angle between the normal vector and the negative incident light vector when both vectors are projected on the xy plane) can be calculated and each one tested for similarity with the gradient, rather than testing all possible normal vectors.

*Note the assignment of "convex" here is arbitrary, because depending on the z component of the light vector, the convexity assumption may result in a concave looking surface in the normal map. Adding to the complexity, sometimes during integration of the normal map the convexity will be reversed again. It is best to examine the depth map at the end and invert it if necessary.*

### Determination of Light Direction
The light direction is assumed to be the direction in which there is the most contrast in slices of the image. (Slice is used here to refer to a vector of pixel values that are in a straight line in the image). This is because the midtone areas tend to be oriented orthogonally (or at least not close to parallel) to the light direction on the image plane. This means when moving along the light direction there will be fewer pixels in the midtones and more pixels in the highlights and shadows. This can be seen the the illustration below.

<img src="images/DepthMapFig22.png" width ="900">

Slicing in the light direction typically yields a distribution that is skewed towards the extreme, while slicing in other directions will result in a distribution that has more intermediate values. This means that the sum of squared deviations from the mean in each slice should be greater in the light direction. This leads to th first component of the light direction desirability score, which is the total sum of squared deviations from the individal slice means (not from the total mean, since that would be the same regardless of slice direction). 

Also notice that adjacent slices are more similar to each other in the direction of the light than in other directions. This leads to the second component of the light direction desirability score, which is the sum of squared deviations from the adjacent slice (calculated for each slice then totalled).

The light direction and the actual geometry of the surface both contribute to the variability of the slices, as can be seen in the following example:

<img src="images/DepthMapFig23.png" width ="300">

The light direction slices (green) have a larger range (more areas of highlights and shadows) than the red slice (more midtones) in the upper part of the figure. However, in the lower part they are about the same. Here the variance is primarily due to the carved lines in the relief. If the entire image were just these lines, then the slice that is parallel to the lines would have little variance. This has nothing to do with the light direction. So the Sobel magnitude in the direction of the slice is used to correct for the surface geometry effect. The Sobel filter is used for edge detection. So the Sobel magnitude in the direction of a slice indicates how perpendicular edges are to the slice. The more perpendicular the edge is, the more contribution there will be due to the edge direction to the overall variance. Therefore the reciprocal of this magnitude is used as a multiplicative correction factor in the desirability score.

The user can adjust the weights (exponents) of the adjacent sum of squares and sobel magnitude in the desirability score. The algorithm calculates this score for all angles and chooses the angle with the largest desirability score. The user can also select how many angles the program will scan (more angles means more resolution on the desirability plot and a more precise output angle).

<img src="images/DepthMapFig17.png" width ="350">

If the user determines that the calculated light direction is not accurate, the user can override the angle.

### Determination of Flat Regions
The angle determined above is the light direction projected onto the xy plane. To obtain the z component additional information is needed. The program calculates this component using the intensity corresponding to flat regions in the image (regions parallel to the image plane, whose surface normal is the z unit vector). In order to determine the intensity for each slice in the direction of the light, the algorithm uses a moving window (of user specified size). For each position of the window, the algorithm calculates the maximum length where the intensity is continuously in the window. 

<img src="images/DepthMapFig13.png" width ="550">

This maximum length is stored for all window positions for all slices. Then the sum across all slices is taken and plotted against the window position.

<img src="images/DepthMapFig18.png" width ="375">

The maximum window position is used as the intensity of the flat region in calculations. The above algorithm is based on the assumption that the flat regions in a bas-relief have the largest areas (corresponding to the unraised background of the relief). This assumption may not always hold. Therefore, the user may override this intensity in the settings window.

### Determination of Cast Shadow Regions
To identify regions that are in cast shadow, the program scans through slices in the direction of the light. Drops in intensity greater than a user defined threshold over a user defined window mark the start of a shadow region, if the pixel intensity after the drop is lower than the midtone intensity (the intensity of the flat region, or a user defined intensity). Increases in intensity greater than another user defined threshold over another user defined window mark the end of a shadow region. 

<img src="images/DepthMapFig14.png" width ="500">

The pixels that are marked as shadow are assigned 1 in a shadow mask, and other pixels are assigned 0. In order to remove noise, any pixel in the mask that is surrounded by at least 6 pixels (out of 8 neighboring pixels) of a different value is assigned that different value.

<img src="images/DepthMapFig20.png" width ="400">

The histogram is generated for all pixels that are marked as shadow.

<img src="images/DepthMapFig19.png" width ="400">

To clean up the shadow mask further, the user can define a threshold fraction. This fraction represents the fraction of total area under the shadow histogram. Any pixel falling under the intensity corresponding to the threshold fraction is included in the shadow mask if not already included. For example if the fraction is set to 0.50, all pixels with values within the 50<sup>th</sup> in the shadow histogram are marked as shadow in the mask.

If the user determines that the shadow mask is inaccurate, the user can override the mask by specifying an intensity below which all pixels will be included in the mask, and above which all pixels will be excluded.

### Mathematical Treatment
For easier calculation of the cosine, the normal vectors and light vectors will all be considered normal. Therefore the cosine is simply the dot product. With all the theory and assumptions above, there are enough equations to calculate the normal vector for lit regions and cast shadow regions separately.

The derivations of the formulas used in this program are rather lengthy, so they are not included in this README file. Refer to the [depth map equations PDF document](DepthMapEquations.pdf) for derivations and final formulas.




