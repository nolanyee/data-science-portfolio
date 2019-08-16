
# Unbeatable Tic-Tac-Toe AI
*Skills: Python, Linear Algebra*

### Overview
This program is a Tic-Tac-Toe AI that has 3 levels of difficulty. The "hard" level is unbeatable. Rather than using the common minimax algorithm, this AI uses a custom deterministic algorithm based on linear algebra. 

First, the gameboard (a 3x3 matrix) is flattened to a 1D matrix of length 9. For each winning path, a vector is created with 1s where the path is, and 0s elsewhere. For example



The state of the game is represented by a similar vector, except that the user's marker (O) is represented by -1 and the computer's (X) is represented by 1. For example


The absolute value of the game state vector indicates which cells are occupied. 

The X Occupancy score is defined as the dot product of a path vector with the game state vector, which indicates the occupancy of Xs in the path minus the occupancy of Os. The Total Occupancy score is defined as the dot product of the path vector with the absolute value of the game state vector, which indicates the total occupancy of the path. A score for each path is assigned (using a dictionary with tuples as keys) based on the values of these two dot products according to the following table.

|X Occupancy|Total Occupancy|Path Score|
|-----------|---------------|----------|
|     2     |       2       |    30    | 
|    -2     |       2       |    10    |
|    -1     |       1       |     2    |
|     0     |       1       |   1.5    |
|    -1     |       0       |     1    |
|     1     |       3       |     0    |
|     1     |       3       |     0    |
|     3     |       3       |     0    |
|    -3     |       3       |     0    |
|     0     |       2       |     0    |




