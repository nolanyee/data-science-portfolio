
# Unbeatable Tic-Tac-Toe AI
*Skills: Python, Linear Algebra*

### Overview
This program is a Tic-Tac-Toe AI that has 3 levels of difficulty. The "hard" level is unbeatable. Rather than using the common minimax algorithm, this AI uses a deterministic algorithm based on linear algebra. 

First, the gameboard (a 3x3 matrix) is flattened to a 1D matrix of length 9. For each winning path, a vector is created with 1s where the path is, and 0s elsewhere. For example the top row path would be \[1,1,1,0,0,0,0,0,0\] and the downward diagonal path would be \[1,0,0,0,1,0,0,0,1\]. 

|#|#|#|
|-|-|-|
| | | |
|-|-|-|
| | | |

The state of the game is represented by a similar vector, except that the user's marker (O) is represented by -1 and the computer's (X) is represented by 1. 


