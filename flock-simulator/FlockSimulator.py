'''
This is a simple simulation of a flock of birds trapped in a box.
Each bird in the flock moves to maintain an optimal distance from its neighbors.
Right-Click to start and stop the animation.
Left-Click to chase the flock around the box.
'''

from tkinter import *
from random import *
from math import *
from numpy.random import multivariate_normal
import time

window = Tk(className = ' Flock')
canvas = Canvas(window, width=1200, height=800)
canvas.pack(fill=BOTH, expand=True )

r = 3 # Bird size
size = 2000 # Flock size
randstep = 5 # Random component of bird movement
ovals = [] # List of birds
directions = [] # Last direction of each bird
dirchange = 0.95 # Contribution from previous direction
predators = None # Predator, which birds will flay away from
predthreshold = 1000 # Distance at which birds will not respond to predators
wallthreshold = 500
lenthreshold = 50 # Maximum length a bird can move at one time
flightthreshold = 20 # Minimum length a bird must fly to stay air born
width = 100 # Optimal bird to bird distance
animating = False # Animation state

# Generates n birds
def generate(n, x, y):
    global ovals
    global directions
    for i in range(n):
        coord = multivariate_normal([x,y],[[size,0],[0,size]])
        ovals.append(canvas.create_oval(coord[0]-r, coord[1]-r, coord[0]+r, coord[1]+r, fill='#000000'))
        directions.append([0,0])

# Calculates direction and magnitude of a bird's flight vector
def neighbors(a):
    global directions
    ovalindex = ovals.index(a)
    vectors = []
    # Maintaining bird to bird distance
    for b in ovals:
        if b !=a:
            xdist = canvas.coords(b)[0] - canvas.coords(a)[0]
            ydist = canvas.coords(b)[1] - canvas.coords(a)[1]
            dist = sqrt(xdist ** 2 + ydist ** 2)
            magnitude = dist - width
            vectors.append([magnitude * xdist / dist, magnitude * ydist / dist])
    # Flying away from box edges
    maxx = canvas.winfo_width()
    maxy = canvas.winfo_height()
    wallxdist1 = maxx - canvas.coords(a)[0]
    wallxdist2 = 0 - canvas.coords(a)[0]
    wallydist1 = maxy - canvas.coords(a)[1]
    wallydist2 = 0 - canvas.coords(a)[1]
    magnitudex = -100000*(1/wallxdist1+1/wallxdist2)
    magnitudey = -100000*(1/wallydist1+1/wallydist2)
    vectors.append([magnitudex, magnitudey])
    # Flying away from predators
    if predators:
        predxdist = predators.x - canvas.coords(a)[0]
        predydist = predators.y - canvas.coords(a)[1]
        if abs(predxdist) < predthreshold or abs(predydist) < predthreshold:
            preddist = sqrt(predxdist ** 2 + predydist ** 2)
            if preddist < predthreshold:
                magnitude = -100000 / preddist
                vectors.append([magnitude *predxdist / preddist, magnitude * predydist / preddist])
    # Final vector is a combination of all components
    final = [0, 0]
    for vector in vectors:
        final[0]+= vector[0]
        final[1] += vector[1]
    final[0]=dirchange * directions[ovalindex][0] + (1-dirchange)*final[0]
    final[1] = dirchange * directions[ovalindex][1] + (1 - dirchange) * final[1]
    # Enforce minimum and maximum flight distance
    length = sqrt(final[0]**2+final[1]**2)
    if length > lenthreshold:
        final[0] *= lenthreshold / length
        final[1] *= lenthreshold / length
    if length < flightthreshold:
        final[0] *= flightthreshold / length
        final[1] *= flightthreshold / length
    directions[ovalindex]=final
    return final

# Move the flock
def move():
    maxx = canvas.winfo_width()
    maxy = canvas.winfo_height()
    for a in ovals:
        vector = neighbors(a)
        xrand = (random()-0.5)*2*randstep
        yrand = (random() - 0.5) * 2 * randstep
        x = xrand + vector[0]
        y = yrand + vector[1]
        # Enforce canvas boundaries
        locx = canvas.coords(a)[0]
        locy = canvas.coords(a)[1]
        if 0<locx+x<maxx and 0<locy+y<maxy:
            canvas.move(a,x,y)
        else:
            canvas.move(a, -x, -y)

# Predator class
class predator():
    def __init__(self,x,y):
        self.x = x
        self.y = y

# Create predator
def attack(event):
    global predators
    predators = predator(event.x, event.y)

# Toggle animation
def movetoggle(event):
    global animating
    global predators
    if not animating:
        animating = True
        while animating:
            move()
            window.update()
            time.sleep(0.001)
    else:
        animating = False

# Bind left and right mouse click
window.bind('<Button-3>',movetoggle)
window.bind('<Button-1>',attack)

# Generate flock
generate(170,600,400)
mainloop()
