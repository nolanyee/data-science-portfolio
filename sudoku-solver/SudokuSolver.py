"""
This program solves any solvable Sudoku puzzle and can generate random solvable puzzles.
Set operations are used to check for validity of entries and recalculate the possible valid values for each cell.
A depth first search approach is used to solve the puzzle, where each valid value of the cell is tested.
To prevent going too far down futile paths, the criterion for moving to the next cell is that the set of
valid values for all remaining cells is not empty. This is verified by recalculating the sets of valid values for
cells in the same row, column, and block as the cell being entered.
"""

numbers = {1,2,3,4,5,6,7,8,9} # Set of possible numbers, used for set operations in order to calculate valid values
solved = False # State of puzzle

from random import *

def reset(): # Resets the puzzle and all associated lists and sets
    global solved
    for i in range(1, 10):
        globals().update({'row' + str(i): [], 'column' + str(i): [], 'block' + str(i): []})
        globals().update(
            {'initialrow' + str(i): set(), 'initialcolumn' + str(i): set(), 'initialblock' + str(i): set()})
        globals().update(
            {'currentrow' + str(i): set(), 'currentcolumn' + str(i): set(), 'currentblock' + str(i): set()})
    solved = False

class cell():
    def __init__(self,row, column, setval=None, trial= None):
        self.row = row
        self.column = column
        self.block = (self.column-1)//3+3*((self.row-1)//3)+1

        globals()['row'+str(self.row)].append(self)
        globals()['column' + str(self.column)].append(self)
        globals()['block' + str(self.block)].append(self)

        self.setval = setval # Value set in original puzzle
        self.trial = trial # Trial value set during puzzle solving
        if not self.setval:
            self.entry = ' '
        else:
            self.entry = self.setval
        self.gamechoices = set() # Set of valid values for a cell based on the original puzzle
        self.currentchoices = set() # Set of valid values for a cell based on the current state of the puzzle

    def updategame(self): # Update self.gamechoices for new or modified puzzle
        if self.setval is None:
            self.gamechoices = numbers.difference(globals()['initialrow' + str(self.row)].union(
                globals()['initialcolumn' + str(self.column)],
                globals()['initialblock' + str(self.block)]))
        else:
            self.gamechoices = set()

    def updatecurrent(self): # Update self.currentchoices during puzzle solving
        if self.setval is None:
            self.currentchoices = numbers.difference(globals()['currentrow' + str(self.row)].union(
                globals()['currentcolumn' + str(self.column)],
                globals()['currentblock' + str(self.block)]))
        else:
            self.currentchoices = set()

    def settrial(self,value): # Set a trial value during puzzle solving
        if self.trial is not None:  # Removes previous value from corresponding set
            globals()['currentrow' + str(self.row)] = \
                globals()['currentrow' + str(self.row)].difference([self.trial])
            globals()['currentcolumn' + str(self.column)] = \
                globals()['currentcolumn' + str(self.column)].difference([self.trial])
            globals()['currentblock' + str(self.block)] = \
                globals()['currentblock' + str(self.block)].difference([self.trial])
        if value in numbers:  # Update cell and set with new value
            self.trial = value
            globals()['currentrow' + str(self.row)] = \
                globals()['currentrow' + str(self.row)].union([self.trial])
            globals()['currentcolumn' + str(self.column)] = \
                globals()['currentcolumn' + str(self.column)].union([self.trial])
            globals()['currentblock' + str(self.block)] = \
                globals()['currentblock' + str(self.block)].union([self.trial])
        else:
            self.trial = None

def initialize(): # Removes all previous puzzle data and creates new empty cell objects
    reset()
    id = 0
    for i in range(1,10):
        for j in range(1,10):
            globals().update({'cell'+str(id):cell(i,j)})
            id +=1

def printboard(): # Prints the puzzle
    for i in range(1,9):
        print(' '+' | '.join([str(x.entry) for x in globals()['row'+str(i)]]))
        print('---+---+---+---+---+---+---+---+---')
    print(' '+' | '.join([str(x.entry) for x in globals()['row9']]))

def entercell(row,column,value,batch=False): # Used for manual cell-wise entry or conversion of array to puzzle
    x = globals()['row' + str(row)][column - 1]
    if value in globals()['initialrow' + str(row)].union(globals()['initialcolumn' + str(column)],
                                                         globals()['initialblock' + str(x.block)]):
        raise Exception('Invalid Puzzle: Conflict') # Raise error if any entry violates the Sudoku rules
    if x.setval in numbers: # Removes previous value from corresponding set
        globals()['initialrow' + str(row)]= globals()['initialrow' + str(row)].difference([x.setval])
        globals()['initialcolumn' + str(column)] = globals()['initialcolumn' + str(column)].difference([x.setval])
        globals()['initialblock' + str(x.block)] = globals()['initialblock' + str(x.block)].difference([x.setval])
    if value in numbers: # Update cell and set with new value
        x.setval = value
        x.entry = value
        globals()['initialrow' + str(row)] = globals()['initialrow' + str(row)].union([x.setval])
        globals()['initialcolumn' + str(column)] = globals()['initialcolumn' + str(column)].union([x.setval])
        globals()['initialblock' + str(x.block)] = globals()['initialblock' + str(x.block)].union([x.setval])
        globals()['currentrow' + str(row)]=globals()['initialrow' + str(row)]
        globals()['currentcolumn' + str(column)]=globals()['initialcolumn' + str(column)]
        globals()['currentblock' + str(x.block)]=globals()['initialblock' + str(x.block)]
    else:
        x.setval = None
        x.entry = ' '
    if not batch:
        for i in range(1, 10):
            for j in range(0, 9):
                globals()['row' + str(i)][j].updategame()

def batchenter(array): # Convert an array to a puzzle
    for i in range(1,10): # Clear previous set values to avoid raising a conflict error
        globals()['initialrow' + str(i)] = set()
        globals()['initialcolumn' + str(i)] = set()
        globals()['initialblock' + str(i)] = set()
    for i in range(0,9): # Transfer the array values into the cells
        for j in range(0,9):
            entercell(i+1,j+1,array[i][j],batch=True)
    for i in range(1, 10): # Update the set of initial valid values for each cell
        for j in range(0, 9):
            globals()['row' + str(i)][j].updategame()

def updateall(): # Update sets of current valid values for all cells
    for i in range(0,81):
        globals()['cell'+str(i)].updatecurrent()
    for i in range(0, 81):
        if globals()['cell'+str(i)].setval is None and globals()['cell'+str(i)].currentchoices == set():
            return False
    return True

def updaterelevant(j): # Update sets of current valid values for all cells affected by cell j
    x = globals()['cell' + str(j)]
    conflicts = 0
    for i in range(j+1,81):
        y = globals()['cell' + str(i)]
        if (y in globals()['row' + str(x.row)] or
                y in globals()['column' + str(x.column)] or
                y in globals()['block' + str(x.block)]) and y.setval is None:
            y.updatecurrent()
            if y.currentchoices == set():
                conflicts +=1
    if conflicts > 0:
        return False
    else:
        return True

def solve(generating = False): # Depth first search algorithm
    def solvesub(i):
        global solved
        x = globals()['cell' + str(i)]
        if x.setval is None:
            if generating: # For puzzle generation the valid values are shuffled for randomness
                choices = list(x.currentchoices)
                shuffle(choices)
            else:
                choices = x.currentchoices
            for j in choices:
                x.settrial(j)
                if updaterelevant(i) and i<80:
                    solvesub(i+1)
                elif i == 80: # solvesub(79) already verified cell 80 has a solution, so the puzzle is solved
                    solved = True
                if solved:
                    x.entry = x.trial
                    break
            if not solved: # To ensure that all trial values are cleared when backtracking to avoid set miscalculations
                x.settrial(None)
        else: # Cells with set values in the original puzzle are skipped.
            if i < 80:
                solvesub(i + 1)
            else: # If the last cell is reached and it is fixed, then the puzzle is solved.
                solved = True
    updateall()
    solvesub(0)
    if solved:
        if generating == False: # To avoid printing during puzzle generation
            print('Solution:')
            printboard()
    else:
        print('No Solution')

def test(x,generating=False):
    initialize()
    batchenter(x)
    if generating == False: # To avoid printing during puzzle generation
        printboard()
    if generating == False:
        solve()
    else: # To avoid printing during puzzle generation
        solve(generating=True)

# Puzzle generation is performed by solving an empty puzzle with randomized lists of valid values for each cell.
# Then cells are randomly set blank based on a specified frequency.

emptypuzzle =[[0,0,0,0,0,0,0,0,0],
              [0,0,0,0,0,0,0,0,0],
              [0,0,0,0,0,0,0,0,0],
              [0,0,0,0,0,0,0,0,0],
              [0,0,0,0,0,0,0,0,0],
              [0,0,0,0,0,0,0,0,0],
              [0,0,0,0,0,0,0,0,0],
              [0,0,0,0,0,0,0,0,0],
              [0,0,0,0,0,0,0,0,0]]

def generatepuzzle(fractionblank): # Fraction blank is the probability that a cell will be set blank
    test(emptypuzzle,generating=True) # Generates random solution to empty puzzle
    newpuzzle = []
    for i in range(1,10): # Transfer data to an array
        newrow = []
        for j in range(0, 9):
            if random() >= fractionblank: # Randomly set cells blank
                newrow.append(globals()['row'+str(i)][j].entry)
            else:
                newrow.append(0)
        newpuzzle.append(newrow)
    print('Generated Puzzle:')
    return newpuzzle

def testrandompuzzle():
    test(generatepuzzle(0.65))

# Example puzzle. Modify as needed.
puzzle = [[5,3,0,0,7,0,0,0,0],
          [6,0,0,1,9,5,0,0,0],
          [0,9,8,0,0,0,0,6,0],
          [8,0,0,0,6,0,0,0,3],
          [4,0,0,8,0,3,0,0,1],
          [7,0,0,0,2,0,0,0,6],
          [0,6,0,0,0,0,2,8,0],
          [0,0,0,4,1,9,0,0,5],
          [0,0,0,0,8,0,0,7,9]]

if __name__ == '__main__':
    randompuzzle = input('Generate Random Puzzle? (yes/no): ')
    if randompuzzle == 'yes':
        testrandompuzzle()
    else:
        print('For each row enter a string of 9 digits, using 0 for blank cells.')
        for i in range(1,10):
            puzzlerow = [int(a) for a in input('Row '+str(i)+'(string of digits) :')]
            puzzle[i-1]=puzzlerow
        test(puzzle)


