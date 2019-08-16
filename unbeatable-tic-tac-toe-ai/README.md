
# Unbeatable Tic-Tac-Toe AI
*Skills: Python, Linear Algebra*

### Overview
This program is a Tic-Tac-Toe AI that has 3 levels of difficulty. The "hard" level is unbeatable. Rather than using the common minimax algorithm, this AI uses a custom deterministic algorithm based on linear algebra. 

First, the gameboard (a 3x3 matrix) is flattened to a 1D matrix of length 9. For each winning path, a vector is created with 1s where the path is, and 0s elsewhere. For example



Each of the path vectors are stacked to form a path matrix __P__, whose entries are shown below.\
1  1  1  0  0  0  0  0  0\
0  0  0  1  1  1  0  0  0\
0  0  0  0  0  0  1  1  1\
1  0  0  1  0  0  1  0  0\
0  1  0  0  1  0  0  1  0\
0  0  1  0  0  1  0  0  1\
1  0  0  0  1  0  0  0  1\
0  0  1  0  1  0  1  0  0

The state of the game is represented by a similar vector, except that the user's marker (O) is represented by -1 and the computer's (X) is represented by 1. For example


The absolute value of the game state vector indicates which cells are occupied. 

The X Occupancy score is defined as the dot product of a path vector with the game state vector, which indicates the occupancy of Xs in the path minus the occupancy of Os. The Total Occupancy score is defined as the dot product of the path vector with the absolute value of the game state vector, which indicates the total occupancy of the path. A score for each path is assigned (using a dictionary with tuples as keys) based on the values of these two dot products according to the following table, which is based on heuristic reasoning.

|X Occupancy|Total Occupancy|Path Score|
|-----------|---------------|----------|
|     2     |       2       |    30    | 
|    -2     |       2       |    10    |
|     1     |       1       |     2    |
|    -1     |       1       |   1.5    |
|     0     |       0       |     1    |
|    -1     |       3       |     0    |
|     1     |       3       |     0    |
|     3     |       3       |     0    |
|    -3     |       3       |     0    |
|     0     |       2       |     0    |

The score of 30 is assigned to the tuple (2,2), which corresponds to the case where the computer has 2 Xs in a path. This is given the highest score because the computer is one move away from winning. The values (-2,2) corresponds to 2 Os in a path, which mean the computer is one move away from losing. It has the second highest score because the computer must block the user from winning. However, it is still lower than (2,2) because if the computer wins first it doesn't matter if the user is one move from winning. 

The tuple (1, 1) corresponds to one X and 2 empty cells in a path. This score is slightly higher than the next two cases because it represents a possible path for the computer to win (it is not blocked by any Os) and the computer needs 2 cells to win. The next tuple (-1, 1) corresponds to one O and 2 empty cells in a path. The score is slightly higher than the next case because the computer has 2 cells in the path that can block the user and advance towards building another path of its own. The tuple (0,0) corresponds to an empty path. This represents a potential path for the computer to win, but since it is unoccupied the computer needs all 3 cells to win, which gives more opportunity for the user to block the path. 

The tuples with Total Occupancy of 3 correspond to paths that are completely occupied, so they have a score of 0. The tuple (0, 2) corresponds to one X and one O in the path. Placing an X here does not block the user since there is already an X in the path, and there is only one possible cell to occupy for the computer. Since there is not much to gain with this path, the score is also 0.

The paths form a row vector __s__ of dimension 8. The total score fo each cell is given by the vector __c__=__P__<sup>T</sup>__s__<sup>T</sup>





