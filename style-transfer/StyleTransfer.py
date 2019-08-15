'''
This program is an implementation of L. A. Gatys, A. S. Ecker, M. Bethge. Image Style Transfer Using Convolutional
Neural Networks. In IEEE Conference on Computer Vision and Pattern Recognition (CVPR), 2016. This implementation
uses TensorFlow. It includes features for fine tuning the loss function by choosing which layers to include in
the style and content loss, and their respective weights. It also allows for adjustment of the relative weight
of style and content in the final result and the number of iterations for gradient descent. The gradient descent is
split into a slow and a fast stage. The slow stage helps mitigate noise generation by being more sensitive to small
gradients at the beginning, so flat areas will descend appropriately. This helps in areas of the picture with little
content information.
'''

# Importing libraries
import tensorflow as tf
import matplotlib.pyplot as plt
from tkinter import *
from tkinter.ttk import *

# Graphic User Interface for Parameter Setting

loopactive=True
window = Tk(className=' Settings')
frame = Frame(window,width=1200, height=800)
frame.pack(fill=BOTH, expand=True )

networklayers = ['block1_conv1','block1_conv2','block1_pool',
                 'block2_conv1','block2_conv2','block2_pool',
                 'block3_conv1','block3_conv2','block3_conv3','block3_conv4','block3_pool',
                 'block4_conv1','block4_conv2','block4_conv3','block4_conv4','block4_pool',
                 'block5_conv1','block5_conv2','block5_conv3','block5_conv4','block5_pool']

def parameterfield(name,description,w,default, default2,r,two = False, offset=0):
    globals().update({name+'label':Label(frame,text=description)})
    globals().update({name + 'entry': Entry(frame, width=w)})
    globals()[name + 'entry'].insert(0,default)
    globals()[name + 'label'].grid(row=r, column = 0+offset, sticky=E)
    globals()[name + 'entry'].grid(row=r, column = 1+offset, sticky=W)
    if two:
        globals().update({name + '2entry': Entry(frame, width=w)})
        globals()[name + '2entry'].insert(0, default2)
        globals()[name + '2entry'].grid(row=r, column=2+offset, sticky=W)

parameterfield('painting','Painting File Path', 80,'','',0,offset=1)
parameterfield('photo','Photograph File Path', 80,'','',1,offset=1)

emptylabel = Label(frame, text='')
emptylabel.grid(row=2, column=0, sticky=W)
headinglabel = Label(frame, text='                   Layer')
headinglabel.grid(row=3, column=0)
headinglabel1 = Label(frame, text='Style Weights')
headinglabel1.grid(row=3, column=1, sticky=W)
headinglabel2 = Label(frame, text='Content Weights')
headinglabel2.grid(row=3, column=2, sticky=W)

# Default Layers
defaultcontentweights = [0,0,0,
                        0,0,0,
                        0,1,0,0,0,
                        0,0,0,0,0,
                        0,0,0,0,0]

defaultstyleweights = [1,0,0,
                        1,0,0,
                        1,0,0,0,0,
                        1,0,0,0,0,
                        1,0,0,0,0]

for i in range(len(networklayers)):
    parameterfield(networklayers[i],networklayers[i],5,defaultstyleweights[i],defaultcontentweights[i],i+4, True)

emptylabel2 = Label(frame, text='')
emptylabel2.grid(row=25, column=0, sticky=W)

parameterfield('paintingscalefactor','Painting Scaling Factor', 5,0.2,'',26,offset=0)
parameterfield('photoscalefactor','Photo Scaling Factor', 5,0.15,'',27,offset=0)
parameterfield('alphabetaratio','Content to Style Ratio', 5,0.05,'',28,offset=0)
parameterfield('learningrate','Stage 1 Learning Rate', 5,0.001,'',29,offset=0)
parameterfield('steps','Stage 1 Gradient Descent Steps', 8,100,'',30,offset=0)
parameterfield('learningrate2','Stage 2 Learning Rate', 5,0.02,'',31,offset=0)
parameterfield('steps2','Stage 1 Gradient Descent Steps', 8,100,'',32,offset=0)

emptylabel3 = Label(frame, text='')
emptylabel3.grid(row=33, column=0, sticky=W)

parameterfield('output','Output File Path', 80,'','',34,offset=1)

emptylabel4 = Label(frame, text='')
emptylabel4.grid(row=35, column=0, sticky=W)

# OK button escapes loop

def done():
    global loopactive
    window.update_idletasks()
    window.withdraw()
    loopactive = False
okbutton =Button(frame, text='OK', command=done)

okbutton.grid(row=36, column = 1, sticky = W)

while loopactive:
    window.update()

# Parameter Setting

# Filepath Input
paintingfile = paintingentry.get()
photofile = photoentry.get()
outputpath = outputentry.get()

# Model Parameters
contentweights = [float(globals()[a+'2entry'].get()) for a in networklayers]

styleweights = [float(globals()[a+'entry'].get()) for a in networklayers]

paintingscalefactor = float(paintingscalefactorentry.get())
photoscalefactor = float(photoscalefactorentry.get())
alphabetaratio = float(alphabetaratioentry.get())
beta = 1

learningrate = float(learningrateentry.get())
learningrate2 = float(learningrate2entry.get())
steps=int(stepsentry.get())
steps2 = int(steps2entry.get())

window.destroy()

# Relevant layers and reduced weight vectors
contentlayers = [networklayers[i] for i in range(21) if contentweights[i] != 0]
stylelayers = [networklayers[i] for i in range(21) if styleweights[i] != 0]
contentreducedwt = [a for a in contentweights if a != 0]
stylereducedwt = [a for a in styleweights if a != 0]
numcontentlayers = len(contentlayers)
numstylelayers = len(stylelayers)

# Loading the images
painting = tf.image.convert_image_dtype(tf.image.decode_image(tf.io.read_file(paintingfile),channels=3), tf.float32)
photo = tf.image.convert_image_dtype(tf.image.decode_image(tf.io.read_file(photofile),channels=3), tf.float32)

# Resizing the images
paintingshape = tf.cast(tf.shape(painting)[:-1], tf.float32)
photoshape = tf.cast(tf.shape(photo)[:-1], tf.float32)
painting = tf.image.resize(painting, tf.cast(paintingscalefactor*paintingshape, tf.int32))
photo = tf.image.resize(photo, tf.cast(photoscalefactor*photoshape, tf.int32))

# Making the image into 4 dimensions (including a sample dimension of value 1)
painting = painting[tf.newaxis, :]
photo = photo[tf.newaxis, :]

# Modeling

# Note a represents the layer, b and c represent 2 filters whose dot product is calculated, i and j are map coordinates
def grammatrix(X):
    return tf.linalg.einsum('aijb,aijc->abc', X, X)/tf.cast(tf.shape(X)[1]*tf.shape(X)[2],tf.float32)

# Combined model
vgg = tf.keras.applications.VGG19(include_top=False, weights='imagenet')
vgg.trainable = False
stylecontentmodel = tf.keras.Model([vgg.input],[vgg.get_layer(x).output for x in (stylelayers+contentlayers)])

# Note that pre-processing includes rescaling values by 1/255, which we don't want,
# so values are multiplied by 255 prior to pre-processing.

def stylecontentevaluate(inputs):
    preprocessed = tf.keras.applications.vgg19.preprocess_input(inputs*255)
    output = stylecontentmodel(preprocessed)
    return [grammatrix(x) for x in output[:numstylelayers]], output[numstylelayers:]

# Target and initial state
styletarget = stylecontentevaluate(painting)[0]
contenttarget = stylecontentevaluate(photo)[1]
variable = tf.Variable(photo)

# Define Loss Function
def loss(outputs):
    styleoutput = outputs[0]
    contentoutput = outputs[1]
    styleloss = tf.add_n([styleweights[i]*tf.reduce_mean((styleoutput[i]-styletarget[i])**2)
                          for i in range(numstylelayers)])/sum(styleweights)
    contentloss = tf.add_n([tf.reduce_mean((contentoutput[i]-contenttarget[i])**2)
                             for i in range(numcontentlayers)])/sum(contentweights)
    return beta*(alphabetaratio*contentloss+styleloss)

# Optimizer
optimizerslow = tf.optimizers.Adam(learning_rate=learningrate, beta_1=0.99, epsilon=1e-1)
optimizerfast = tf.optimizers.Adam(learning_rate=learningrate2, beta_1=0.99, epsilon=1e-1)

# Gradient Descent
@tf.function()
def stylizestep(image):
    with tf.GradientTape() as tape:
        optimizerslow.apply_gradients([(tape.gradient(loss(stylecontentevaluate(image)), image), image)])
    image.assign(tf.clip_by_value(image, clip_value_min=0.0, clip_value_max=1.0))

@tf.function()
def stylizestepfast(image):
    with tf.GradientTape() as tape:
        optimizerfast.apply_gradients([(tape.gradient(loss(stylecontentevaluate(image)), image), image)])
    image.assign(tf.clip_by_value(image, clip_value_min=0.0, clip_value_max=1.0))

for i in range(steps):
    stylizestep(variable)
for i in range(steps2):
    stylizestepfast(variable)

# Previewing the images
fig, ax = plt.subplots(2,2)
ax[0,0].imshow(tf.squeeze(painting, axis=0))
ax[0,0].set_title('Style Image')
ax[0,1].imshow(tf.squeeze(photo, axis=0))
ax[0,1].set_title('Content Image')
ax[1,0].imshow(variable.read_value()[0])
ax[1,0].set_title('Style Transfer Result')
fig.delaxes(ax[1,1])
fig.set_size_inches(16, 9)
plt.tight_layout()
plt.show()

# Save the file
result = tf.io.encode_jpeg(tf.dtypes.cast(variable.read_value()[0]*255,tf.uint8))
tf.io.write_file(outputpath,result)