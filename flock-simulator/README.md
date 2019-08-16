# Flock Simulator
*Skills: Python, Linear Algebra*

### Overview
This program simulates a flock of birds in flight (or perhaps a swarm of bees). The birds are trapped in the window and fly around. The user can act as a predator and chase the birds around the window.

<img src="images/Flock1.jpg" width = "400">

### Usage
Right-Click to start and stop the animation.


Left-Click to chase the flock around the box.

<img src="images/Flock2.jpg" width = "400">

### Technical Details
The velocity of each bird in the flock is calculated from the distance between the bird and other birds in the flock, the distance between the bird and the walls of the window, and the distance between the bird and the predator. Beacuse birds cannot change direction that fast, the overall velocity is a weighted sum of the above factors and the previous velocity. Finally, a random component to the velocity is added. In addition, the birds have a minumum and maximum velocity magnitude they must maintain, so the magnitude of the velocity vectors is adjusted if the calculated velocity falls out of the range.

Some fine tuning was involved in developing the mathematical formulation for the bird velocity, in an attempt to reproduce results similar to those observed in nature. For the mathematical details, see [FlockEquations](FlockEquations.pdf)
