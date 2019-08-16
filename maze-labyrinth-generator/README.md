# Maze and Labyrinth Generator
*Skills: Python, Algorithms, Data Structures*

### Overview
This program generates and solves random mazes and labyrinths of variable size. It also allows the user to move a turtle around the maze and has a toggle button to show and hide the solution.

The difference between a maze and a labyrinth is that a labyrinth has only one path and no forks. There are plenty of widely known algorithms for maze generation, but not so much for labyrinth generation. This program uses a unique algorithm for labyrinth generation that involves the use of circular list data structures, which outperforms a depth first search type algorithm. 

The maze generation algorithm uses a disjoint set data structure. 

The program also includes a unique grid type maze, where each grid block is a labyrinth (this algorithm uses depth first search rather than circular lists to generate the mini labyrinths because they are small). Then the grid blocks are treated like disjoint sets and combined to form the overall maze.

The mazes are solved using Dijkstra's algorithm.

### Maze Generation


### Labyrinth Generation


### Grid Maze Generation

