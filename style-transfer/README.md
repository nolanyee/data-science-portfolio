# Style Transfer Implementation
*Skills: Python, Image Processing, Convolutional Neural Networks, Gradient Descent*

This program is an implementation of the paper L. A. Gatys, A. S. Ecker, M. Bethge. Image Style Transfer Using Convolutional Neural Networks. In IEEE Conference on Computer Vision and Pattern Recognition (CVPR), 2016. For technical details, refer to the paper. This implementation uses TensorFlow and VGG-19, a pre-trained convolutional neural network.

It includes features for fine tuning the loss function by choosing which layers to include in the style and content loss, and their respective weights. It also allows for adjustment of the relative weight of style and content in the final result and the number of iterations for gradient descent. 

The gradient descent is split into a slow and a fast stage. The slow stage helps mitigate noise generation by being more sensitive to small gradients at the beginning, so flatter areas will descend appropriately and consistently. This helps in areas of the picture with little content information.

