'''
This program plays Tic-Tac-Toe with the user using an algorithm based on linear algebra, as an alternative to minimax.

Hard mode is deterministic. Easy and medium modes have randomness introduced so the computer can make mistakes.
Running the built-in test procedure proves that it is impossible for user to win in hard mode.

9 cells referenced by column a, b, c and row 1, 2, 3
8 paths are columns a, b, c, rows 1, 2, 3 and the downward and upward diagonals
User is O (coded as -1), computer is X (coded as 1), empty cell is coded as 0
'''

# Matrix relating cell position (columns) to associated paths (rows)
cellpath = [[1, 1, 1, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 1, 1, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 1, 1, 1],
            [1, 0, 0, 1, 0, 0, 1, 0, 0],
            [0, 1, 0, 0, 1, 0, 0, 1, 0],
            [0, 0, 1, 0, 0, 1, 0, 0, 1],
            [1, 0, 0, 0, 1, 0, 0, 0, 1],
            [0, 0, 1, 0, 1, 0, 1, 0, 0]]

# Dictionary relates user input to vector index
cellvector = {'a1':0,'b1':1,'c1':2,'a2':3,'b2':4,'c2':5,'a3':6,'b3':7,'c3':8}

# Dictionary relates computer mode to difficulty constants
difficulty = {'easy': 1.5, 'medium': 1.1, 'hard':0}

# Dot product for row vectors
def dot(x, y):
    return sum(i*j for i, j in zip(x, y))

# Entry-wise absolute value for row vector
def absrow(x):
    return [abs(i) for i in x]

# Decodes game vector and populates entries in board
def printboard():
    decode=[]
    for i in range(0, 9):
        if game[i] == 1:
            decode.append('X')
        elif game[i] == -1:
            decode.append('O')
        elif game[i] == 0:
            decode.append(' ')
    print('  a   b   c \n1 {} | {} | {} \n ---+---+---\n2 {} | {} | {} \n ---+---+---\n3 {} | {} | {} '.format(*decode))

# User input procedure
def userinput():
    global game
    usermove=input('Your turn. Enter cell reference: ')
    while (usermove not in list(cellvector.keys())) or (game[cellvector[usermove]] != 0):
        if usermove == 'quit':
            break
        elif usermove not in list(cellvector.keys()):
            print('Invalid reference')
            usermove = input('Enter cell reference: ')
        elif game[cellvector[usermove]] != 0:
            print('Already occupied')
            usermove = input('Enter cell reference: ')
    if usermove == 'quit':
            return 'quit'
    else:
        game[cellvector[usermove]] = -1
        printboard()

# Path scoring procedure is based on Xs - Os and on the number of occupied cells in the path.
def pathscore():
    pathscorevector=[]
    scoredict = {(2, 2): 30 - difficulty[level]*random()*20, # 2 Xs and 1 empty
                 (-2, 2): 10 - difficulty[level]*random()*5, # 2 Os and 1 empty
                 (1, 1): 2 + difficulty[level]*random()*1, # 1 X and 2 empty
                 (-1, 1): 1.5 + difficulty[level]*random()*1.5, # 1 O and 2 empty
                 (0, 0): 1 + difficulty[level]*random()*2, # 3 empty
                 (-1, 3): 0 + difficulty[level]*random()*3, # 2 Os and 1 X
                 (1, 3): 0 + difficulty[level]*random()*3, # 2 Xs and 1 O
                 (3, 3): 0 + difficulty[level]*random()*3, # 3 Xs
                 (-3, 3): 0 + difficulty[level]*random()*3, # 3 Os
                 (0, 2): 0 + difficulty[level]*random()*3} # 1 X and 1 O, 1 empty
    for i in range(0, 8):
        pcoord = (dot(cellpath[i],game), dot(cellpath[i],absrow(game)))
        pscore = scoredict[pcoord]
        pathscorevector.append(pscore)
    return pathscorevector

# Cell scoring procedure, calculated from path scores.
def cellscore():
    p = pathscore()
    boardscore = []
    for i in range(0,9):
        if game[i]== 0:
            boardscore.append(dot(list(list(zip(*cellpath))[i]),p) + difficulty[level]*random()*6)
        else:
            boardscore.append(-1) #ensures that occupied cells will not be chosen
    return boardscore

# Note that in hard mode the algorithm is completely deterministic. This results in only 1329 possible games.
# Based on the scoring defined above, testing shows the computer can lose 4 out of 1329 games. The score is
# therefore overridden in those specific scenarios to block the user from winning.

# Computer move procedure
def computermove():
    global game
    if level == 'hard' and game in ([-1,0,0,0,1,0,0,0,-1],[0,0,-1,0,1,0,-1,0,0]):
        moveindex = 1
    else:
        moveindex = max(enumerate(cellscore()),key = lambda x : x[1])[0]
    game[moveindex] = 1
    printboard()

# Detect win
def win():
    w = 0
    for i in range(0, 8):
        pcoord = [dot(cellpath[i],game), dot(cellpath[i],absrow(game))]
        if pcoord == [-3, 3]: #3 Os
            w = -1
        elif pcoord == [3, 3]: #3 Xs
            w = 1
    return w

# One Game Cycle
def gamecycle():
    global userpoints
    global computerpoints
    global tie
    while True:
        if userinput() == 'quit':
            return 'quit'
        elif win() == -1:
            print('You Win!')
            userpoints += 1
            break
        elif win() == 0 and 0 not in game:
            print('Tie.')
            tie += 1
            break
        computermove()
        if win() == 1:
            print('You Lose.')
            computerpoints += 1
            break
        elif win() == 0 and 0 not in game:
            print('Tie.')
            tie += 1
            break

# Create new iterator over a list to explore all possible moves for testing
class listiter:
    def __init__(self,x = None):
        self.list = x
        self.base = [1]
        n=len(self.list)
        for i in range(0, n):
            self.base.append(self.base[i]*self.list[n-1-i])
        self.base.reverse()
        self.i = -1

    def __iter__(self):
        return self

    def __next__(self):
        if self.i + 1 < self.base[0]:
            self.i += 1
            imod = [self.i%self.base[0]]
            nextlist = []
            for j in range(1,len(self.list)):
                imod.append(imod[j-1]%self.base[j])
            for k in range(0,len(self.list)):
                nextlist.append(imod[k]//self.base[k+1])
            return nextlist
        else:
            raise StopIteration

# Number of moves available at each turn, depending on who starts first
testdict = {0:[9, 7, 5, 3, 1], 1:[8, 6, 4, 2]}

# Test User Moves, exploring all possible paths based on the state of the iterator
def testinput():
    global game
    freespaces = []
    for i in range(0,9):
        if game[i] == 0:
            freespaces.append(i)
    testmove = freespaces[l[testdict[start].index(len(freespaces))]]
    game[testmove] = -1
    printboard()

# Test Cycle
def testcycle():
    global userpoints
    global computerpoints
    global tie
    while True:
        testinput()
        if win() == -1:
            print('Test Wins!')
            userpoints += 1
            break
        elif win() == 0 and 0 not in game:
            print('Tie.')
            tie += 1
            break
        computermove()
        if win() == 1:
            print('Test Loses.')
            computerpoints += 1
            break
        elif win() == 0 and 0 not in game:
            print('Tie.')
            tie += 1
            break

# Test Procedure explores all possible moves against the computer when computer goes second or first
def test():
    global game
    global l
    global start
    game = [0, 0, 0, 0, 0, 0, 0, 0, 0]
    start = 0
    for l in listiter(testdict[start]):
        printboard()
        testcycle()
        print(str(userpoints) + ' wins, ' + str(computerpoints) + ' losses, ' + str(tie) + ' ties.')
        game = [0, 0, 0, 0, 0, 0, 0, 0, 0]
    start = 1
    for l in listiter(testdict[start]):
        printboard()
        computermove()
        testcycle()
        print(str(userpoints) + ' wins, ' + str(computerpoints) + ' losses, ' + str(tie) + ' ties.')
        game = [0, 0, 0, 0, 0, 0, 0, 0, 0]

if __name__ == '__main__':
    from random import *
    level = input('Choose difficulty level (easy, medium, hard): ')
    userpoints, computerpoints, tie = 0, 0, 0
    status = 'play'
    while level not in list(difficulty.keys()):
        if level == 'test':
            level = 'hard'
            status = 'test'
            test()
        else:
            print('Invalid choice.')
            level = input('Choose difficulty level (easy, medium, hard): ')
    if status == 'play':
        print('You are O, the computer is X.')
        print('Input your move by typing the column letter (lowercase) and row number (no spaces)')
        game = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        start = randint(0,1) # randomly decides who will have the first move
        while True:
            printboard()
            if start == 1:
                print('Computer goes first.')
                computermove()
            if gamecycle() == 'quit':
                break
            print(str(userpoints)+' wins, '+str(computerpoints)+' losses, '+str(tie)+' ties.')
            continued = input('Do you want to play again? (yes/no): ')
            if continued != 'yes':
                break
            start = int(-(start-0.5)+0.5) # alternates between user and computer having the first move
            game = [0, 0, 0, 0, 0, 0, 0, 0, 0]
