'''
This is a simple straight heads-up poker game. The player and computer are each dealt a 5 card hand, with no drawing.
The algorithm uses card counting, combinatorics, probability, Bayes theorem, logistic regression, and heuristics.

The computer cannot 'see' the player's cards except if they are revealed at the end of a showdown. The computer card
counts to determine the probability of the player having a better hand. At any stage in betting, the computer
calculates the probability threshold for which the expectation value of money won is 0, then creates a default average
cumulative probability curve for folding.

The player's cumulative probability of folding is generated using logistic regression on the last 100 player actions.
By comparing the mean cumulative probability to the player's model, the computer determines if the player is cautious
or aggressive, and estimates the probability the player is bluffing or will fold prematurely. Using Bayes theorem,
the computer recalculates the probability that the player will be under the threshold probability. This is used to
update the probability that the player will have a hand that beats the computer's hand. If the probability that the
computer's hand is higher plus the probability that the player's hand is higher and the player folds is lower than the
threshold, the computer may raise. The frequency of raising is determined by how good the computer's hand is and/or
how many successful showdowns have occurred.
'''

from random import *
from sklearn.linear_model import LogisticRegression
from scipy.special import comb
from scipy.stats import beta
from itertools import *
from math import e
from collections import deque

number = {1:'A',2:'2',3:'3',4:'4',5:'5',6:'6',7:'7',8:'8',9:'9',10:'10',11:'J',12:'Q',13:'K',14:'A'}
symbol={'spade':'\u2660','heart':'\u2665','diamond':'\u2666','club':'\u2663'}
ranking = {'spade':4,'heart':3,'diamond':2,'club':1}
invranking = {4:'spade',3:'heart',2:'diamond',1:'club'}
handranking = ['nopair','onepair','twopair','threekind','straight','flush','fullhouse','fourkind','straightflush']

# Product Function
def product(x):
    y = 1
    for i in x:
        y = y*i
    return y

# Card class
class card():
    def __init__(self,suit,value):
        self.suit = suit
        self.value = value
        self.rank = (self.value-2)*4+ranking[self.suit]
    def printcard(self):
        print(number[self.value]+symbol[self.suit])

#  Pile of cards
class pile():
    def __init__(self):
        self.cards = []
        self.size = 0
    def shuffle(self):
        shuffle(self.cards)
    def draw(self):
        self.size -= 1
        return self.cards.pop()
    def place(self,card):
        self.cards.append(card)
        self.size+=1

# Deck of cards
class deck(pile):
    def __init__(self): # Initializes with all 52 cards
        super().__init__()
        for i in ['spade','heart','diamond','club']:
            for j in range(2,15):
                if str(j)+i not in globals().keys(): # Prevents creating duplicate cards for computer deck
                    globals().update({str(j)+i:card(i,j)})
                self.cards.append(globals()[str(j)+i])
        self.size = 52
        self.calccomb()

    def valuecount(self): # Stores counts of each card value
        self.valuedict = {2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0, 11: 0, 12: 0, 13: 0, 14:0}
        for x in [a.value for a in self.cards]:
            self.valuedict[x]+=1

    def straightflush(self): # Combinations of a straight flush given a deck
        self.straightflushcomb = {} # List of highest card in hand and probability of associated straight flush
        for i in ['spade', 'heart', 'diamond', 'club']:
            for j in range(2, 15):
                if j >= 5 and globals()[str(j) + i] in self.cards: # Note: 2-4 cannot be the highest card
                    counter = 0
                    for k in range(j-4, j): # The required 4 preceding values for a straight flush
                        if k != 1: # Aces counted as 14
                            if globals()[str(k) + i] in self.cards: # Counts if card is present in deck
                                counter += 1
                    if j == 5 and globals()[str(14) + i] in self.cards: # For the case of A 2 3 4 5, where 5 is high
                        counter += 1
                    self.straightflushcomb.update({str(j) + i: counter//4}) # All 4 cards must be present
                else:
                    self.straightflushcomb.update({str(j) + i: 0})

    # Combos of a flush is the number of choices of 4 cards from however many are lower than the high of that suit
    def flush(self):
        self.flushcomb = {}
        for i in ['spade', 'heart', 'diamond', 'club']:
            for j in range(2, 15):
                if j>=6 and globals()[str(j) + i] in self.cards: # Since A is 14, high card is never lower than 6
                    counter  = 0
                    for k in range(2, j): # Count all cards lower than the high card with the same suit
                        if globals()[str(k)+i] in self.cards:
                            counter += 1
                    if j == 14: # Subtract straight flushes and case of A 2 3 4 5 for Ace
                        self.flushcomb.update({str(j) + i: comb(counter, 4)
                                             - self.straightflushcomb[str(5) + i]- self.straightflushcomb[str(j) + i]})
                    else: # For others subtract combinations that are straight flushes
                        self.flushcomb.update({str(j) + i: comb(counter, 4)-self.straightflushcomb[str(j) + i]})
                else:
                    self.flushcomb.update({str(j) + i: 0})

    # Combos of a straight is the product of the number of each card of required value
    def straight(self):
        self.straightcomb = {}
        for i in ['spade', 'heart', 'diamond', 'club']:
            for j in range(2, 15):
                if j >= 5 and globals()[str(j) + i] in self.cards: # Note: 2-4 cannot be the highest card
                    counts = []
                    for k in range(j - 4, j): # Create a list of numbers of cards of required value
                        if k != 1:
                            if self.valuedict[k] > 0:
                                counts.append(self.valuedict[k])
                    if j == 5 and self.valuedict[14]>0: # For A 2 3 4 5, include count for Ace (recorded as 14)
                        counts.append(self.valuedict[14])
                    self.straightcomb.update({str(j) + i: (len(counts) // 4)*product(counts)
                                                          -self.straightflushcomb[str(j) + i]}) #Subtract straight flush
                else:
                    self.straightcomb.update({str(j) + i: 0})

    # Combos given a high card, is sum of products of number of cards of each value, over combinations of size 4
    def nopair(self):
        self.nopaircomb = {}
        for i in ['spade', 'heart', 'diamond', 'club']:
            for j in range(2, 15):
                if j >= 6 and globals()[str(j) + i] in self.cards:
                    counts = []
                    for k in range(2, j):
                        if self.valuedict[k] > 0:
                            counts.append(self.valuedict[k])
                    combos = 0
                    for a in combinations(counts,4):
                        combos = combos + product(a)
                    if j ==  14: # Subtract straight flush, flush, and straight probabilities
                        self.nopaircomb.update({str(j) + i: combos - self.straightflushcomb[str(j) + i]
                            - self.flushcomb[str(j) + i] - self.straightcomb[str(j) + i]
                            - self.straightflushcomb[str(5) + i] - self.straightcomb[str(5) + i]})
                    else:
                        self.nopaircomb.update({str(j)+i: combos
                        -self.straightflushcomb[str(j) + i]-self.flushcomb[str(j) + i]-self.straightcomb[str(j) + i]})
                else:
                    self.nopaircomb.update({str(j) + i: 0})

    # Combos of full house
    def fullhouse(self):
        self.fullhousecomb = {}
        for i in ['spade', 'heart', 'diamond', 'club']:
            for j in range(2, 15):
                if j>= 3 and globals()[str(j) + i] in self.cards: # If the high card is in the triplet
                    high3comb = 0
                    if self.valuedict[j]>=3:
                        paircount = 0
                        for k in range(2,j):
                            if self.valuedict[k]>=2: # Combinations of pairs of lower value than the triplet
                                paircount += comb(self.valuedict[k],2)
                        count = 0
                        for m in range(1,ranking[i]): # Combinations of suits for the triplet
                            if globals()[str(j)+invranking[m]] in self.cards:
                                count +=1
                        high3comb = comb(count,2)*paircount
                    high2comb = 0
                    if self.valuedict[j] >= 2: # If the high card is in the pair
                        triplecount = 0
                        for k in range(2, j):
                            if self.valuedict[k] >= 3: # Combinations of triplets lower than the pair
                                triplecount += comb(self.valuedict[k], 3)
                        count = 0
                        for m in range(1, ranking[i]): # Combinations of suits for the pair
                            if globals()[str(j) + invranking[m]] in self.cards:
                                count += 1
                        high2comb = comb(count, 1) * triplecount
                    self.fullhousecomb.update({str(j)+i:high2comb+high3comb}) # Total combinations
                else:
                    self.fullhousecomb.update({str(j) + i: 0})

    # Combos of a full house containing a triplet (not necessarily having the high card in the triplet)
    def fullhouse3(self): # For use in calculating combinations of three of a kind
        self.fullhouse3comb = {}
        for i in ['spade', 'heart', 'diamond', 'club']:
            for j in range(2, 15):
                if globals()[str(j) + i] in self.cards:
                    high3comb = 0
                    if self.valuedict[j]>=3:
                        paircount = 0
                        for k in range(2,j): # combinations of lower pairs
                            if self.valuedict[k]>=2:
                                paircount += comb(self.valuedict[k],2)
                        for k in range(j+1,15): # combinations of higher pairs
                            if self.valuedict[k]>=2:
                                paircount += comb(self.valuedict[k],2)
                        count = 0
                        for m in range(1,ranking[i]): # combinations of suits for the triplet
                            if globals()[str(j)+invranking[m]] in self.cards:
                                count +=1
                        high3comb = comb(count,2)*paircount
                    self.fullhouse3comb.update({str(j)+i:high3comb})
                else:
                    self.fullhouse3comb.update({str(j) + i: 0})

    # Combinations of four of a kind, if all 4 in are in the deck, is just the number of remaining cards in the deck
    def fourkind(self):
        self.fourkindcomb={}
        for i in ['spade', 'heart', 'diamond', 'club']:
            for j in range(2, 15): # Note that the high card in a four of a kind is always a spade
                if self.valuedict[j] ==4 and i == 'spade':
                    self.fourkindcomb.update({str(j) + i:self.size-4})
                else:
                    self.fourkindcomb.update({str(j) + i: 0})

    # Combos for 3 of a kind is the combination of suits tiems combos for the remaining 2 cards
    def threekind(self):
        self.threekindcomb = {}
        for i in ['spade', 'heart', 'diamond', 'club']:
            for j in range(2, 15):
                if globals()[str(j) + i] in self.cards and self.valuedict[j] >= 3:
                    count = 0
                    for m in range(1, ranking[i]): # Combinations of suits for the triplet
                        if globals()[str(j) + invranking[m]] in self.cards:
                            count += 1 # Then subtract combos for four of a kind and full house containing the triplet
                    self.threekindcomb.update({str(j) + i:comb(count,2)*comb(self.size-3,2)
                        -self.fourkindcomb[str(j) + 'spade']-self.fullhouse3comb[str(j) + i]})
                else:
                    self.threekindcomb.update({str(j) + i: 0})

    # Combos for 2 pair is the combos for the suits of the high pair times combos for lower pair
    def twopair(self):
        self.twopaircomb = {}
        for i in ['spade', 'heart', 'diamond', 'club']:
            for j in range(2, 15):
                if globals()[str(j) + i] in self.cards and self.valuedict[j] >= 2:
                    count =0
                    for m in range(1, ranking[i]): # Combinations of suits for high pair
                        if globals()[str(j) + invranking[m]] in self.cards:
                            count += 1
                    paircount = 0
                    for k in range(2, j): # Combinations for lower pair
                        if self.valuedict[k] >= 2:
                            paircount += comb(self.valuedict[k], 2)*\
                                         (self.size-4-(self.valuedict[j]-2)-(self.valuedict[k]-2))
                    self.twopaircomb.update({str(j) + i:comb(count, 1) * paircount})
                else:
                    self.twopaircomb.update({str(j) + i: 0})

    # Combos for a pair is combos for suits of the pair times combinations of other 3 cards (see no pair calculation)
    def onepair(self):
        self.onepaircomb = {}
        for i in ['spade', 'heart', 'diamond', 'club']:
            for j in range(2, 15):
                if globals()[str(j) + i] in self.cards and self.valuedict[j] >= 2:
                    count = 0
                    for m in range(1, ranking[i]): # Combos of suits for the pair
                        if globals()[str(j) + invranking[m]] in self.cards:
                            count += 1
                    counts = []
                    for k in range(2, j): # Counts of cards lower than pair
                        if self.valuedict[k] > 0:
                            counts.append(self.valuedict[k])
                    for k in range(j+1, 15): # Counts of cards higher than pair
                        if self.valuedict[k] > 0:
                            counts.append(self.valuedict[k])
                    combos = 0
                    for a in combinations(counts, 3): # All possible combinations of 3 different values
                        combos = combos + product(a)
                    self.onepaircomb.update({str(j) + i:comb(count, 1)*combos})
                else:
                    self.onepaircomb.update({str(j) + i:0})

    def calccomb(self): # Calculate the combinations
        self.valuecount()
        self.straightflush()
        self.flush()
        self.straight()
        self.nopair()
        self.fullhouse()
        self.fullhouse3()
        self.fourkind()
        self.threekind()
        self.twopair()
        self.onepair()

    def combos(self,type): # Function returning the combinations of specified hand
        if type == 'straightflush':
            return self.straightflushcomb
        elif type == 'flush':
            return self.flushcomb
        elif type == 'straight':
            return self.straightcomb
        elif type == 'nopair':
            return self.nopaircomb
        elif type == 'fullhouse':
            return self.fullhouse3comb
        elif type == 'fourkind':
            return self.fourkindcomb
        elif type == 'threekind':
            return self.threekindcomb
        elif type == 'twopair':
            return self.twopaircomb
        elif type == 'onepair':
            return self.onepaircomb


    def totalprob(self,type): # Function returning the probability of specified hand
        if type == 'straightflush':
            return sum(self.straightflushcomb.values())/comb(self.size,5)
        elif type == 'flush':
            return sum(self.flushcomb.values())/comb(self.size,5)
        elif type == 'straight':
            return sum(self.straightcomb.values())/comb(self.size,5)
        elif type == 'nopair':
            return sum(self.nopaircomb.values())/comb(self.size,5)
        elif type == 'fullhouse':
            return sum(self.fullhouse3comb.values())/comb(self.size,5)
        elif type == 'fourkind':
            return sum(self.fourkindcomb.values())/comb(self.size,5)
        elif type == 'threekind':
            return sum(self.threekindcomb.values())/comb(self.size,5)
        elif type == 'twopair':
            return sum(self.twopaircomb.values())/comb(self.size,5)
        elif type == 'onepair':
            return sum(self.onepaircomb.values())/comb(self.size,5)

class hand(): # Class of 5 card hands
    def __init__(self,cards):
        self.cards = sorted(cards,key = lambda x:x.rank) # Sorted by value of card and suit
        self.type = None # Type of hand
        self.max = None # High card in hand

    def append(self,card): # Add a card to the hand
        self.cards.append(card)
        self.cards = sorted(self.cards,key = lambda x:x.rank)

    def printhand(self): # Print the hand
        print(' '+number[self.cards[0].value]+symbol[self.cards[0].suit]+' '
              +number[self.cards[1].value]+symbol[self.cards[1].suit]+' '
              +number[self.cards[2].value]+symbol[self.cards[2].suit]+' '
              +number[self.cards[3].value]+symbol[self.cards[3].suit]+' '
              +number[self.cards[4].value]+symbol[self.cards[4].suit]+' ')

    def classify(self): # Classify the hand (assign a type)
        suits = set([x.suit for x in self.cards])
        values = [x.value for x in self.cards]
        valuecount = {} # A dictionary of the number of each value in the hand
        maxrep = 0 # The maximum number of any value in the hand
        for value in values:
            if value not in valuecount.keys():
                valuecount.update({value:1})
            else:
                valuecount[value]+=1
            if valuecount[value]>maxrep:
                maxrep = valuecount[value]
        if len(suits)==1 and (max(values)-min(values))==4: # Straight flush has only 1 suit and high - low = 4
            self.type = 'straightflush'
            self.max = max(self.cards,key = lambda x:x.rank) # High is the maximum in the hand
        elif len(suits)==1 and {2,3,4,5,14}==set(values): # For the case of A 1 2 3 4 5
            self.type = 'straightflush'
            self.max = globals()[str(5)+self.cards[3].suit] # When sorted, the 5 has index 3
        elif len(suits)==1: # Flush has only 1 suit
            self.type = 'flush'
            self.max = max(self.cards, key=lambda x: x.rank) # High is the maximum in the hand
        elif (max(values)-min(values))==4 and len(valuecount)==5: # Straight has 5 different values and high - low = 4
            self.type = 'straight'
            self.max = max(self.cards, key=lambda x: x.rank) # High is the maximum in the hand
        elif {2,3,4,5,14}==set(values): # For the case of A 1 2 3 4 5
            self.type = 'straight'
            self.max = globals()[str(5) + self.cards[3].suit]
        elif maxrep == 4: # The maximum number of cards for a value is 4
            self.type = 'fourkind'
            self.max = globals()[str(values[2]) + 'spade']
        elif maxrep == 3 and len(valuecount)==2: # The maximum number of cards for a value is 3, and 2 different values
            self.type = 'fullhouse'
            self.max = max(self.cards, key=lambda x: x.rank) # High is the maximum in the hand
        elif maxrep == 3 and len(valuecount) == 3:# The maximum number of cards for a value is 3, and 3 different values
            self.type = 'threekind'
            self.max =  max([x for x in self.cards if valuecount[x.value]==3], key=lambda x: x.rank) # Max of the 3
        elif maxrep == 2 and len(valuecount) == 3: # The maximum number for a value is 2, and 3 different values
            self.type = 'twopair'
            self.max = max([x for x in self.cards if valuecount[x.value] == 2], key=lambda x: x.rank) # Max of 2 pairs
        elif maxrep == 2 and len(valuecount) == 4: # The maximum number for a value is 2, and 4 different values
            self.type = 'onepair'
            self.max = max([x for x in self.cards if valuecount[x.value] == 2], key=lambda x: x.rank) # Max of the pair
        else:
            self.type = 'nopair'
            self.max = max(self.cards,key = lambda x:x.rank) # High is the maximum in the hand

def playerprob(deck, hand): # probability of player getting better hand than computer
    prob = 0
    hand.classify() # Classify the computer's hand
    for i in range (handranking.index(hand.type)+1,len(handranking)): # Calculate probability of higher hands
        prob += deck.totalprob(handranking[i])
    for i in ['spade', 'heart', 'diamond', 'club']: # Calculate probability of same hand but higher high card
        for j in range(2, 15):
            if globals()[str(j) + i].rank > hand.max.rank:
                prob += deck.combos(hand.type)[str(j) + i]/comb(deck.size,5)
    return prob

def beathand(hand1, hand2): # returns True if hand 1 beats hand 2
    hand1.classify()
    hand2.classify()
    if handranking.index(hand1.type)>handranking.index(hand2.type) or\
        (handranking.index(hand1.type) == handranking.index(hand2.type) and hand1.max.rank > hand2.max.rank):
        return True
    else:
        return False

def deal(): # Deal cards to player and computer
    global playerhand
    global comphand
    global maindeck
    global compdeck
    global compamount
    global playeramount
    global pot
    playerhand = hand([])
    for i in range(0, 5): # Cards drawn
        playerhand.append(maindeck.draw())
    comphand = hand([])
    for i in range(0, 5):
        comphand.append(maindeck.draw())
    for x in comphand.cards:
        compdeck.cards.remove(x)
    playerhand.printhand() # Print player's hand
    print('')
    compamount -= minbet # Minimum bet in the pot
    playeramount -= minbet
    pot += minbet*2

def endround(): # Procedure for ending a round
    global playerhand
    global comphand
    global discard
    global lastmoves
    global pot
    global compamount
    global playeramount
    global totalplayerbet
    global totalcompbet
    global first
    # If both call or if one runs out of money, compare hands to determine who gets the pot
    if (lastmoves[0] == 'call' and lastmoves[1] == 'call') or\
            ((compamount <=0 or playeramount <=0) and lastmoves[1]!='fold'):
        if beathand(comphand, playerhand):
            compamount += pot
        else:
            playeramount +=pot
        pot = 0
        showhands()
        printamounts()
    for x in playerhand.cards: # Add cards to discard pile
        discard.place(x)
    for x in comphand.cards:
        discard.place(x)
    playerhand = hand([]) # Empty the hands
    comphand = hand([])
    lastmoves = deque([],2) # Reset move queue
    totalplayerbet = 0 # Reset total player and computer bet amounts
    totalcompbet = 0
    if first != 'player':
        first = 'player'
    else:
        first = 'computer'

def showhands(): # For a showdown
    global comphandsrevealed
    global compwinsrevealed
    for x in playerhand.cards: # Revealed player's card gets removed from computer's 'remembered' deck
        compdeck.cards.remove(x)
    comphandsrevealed +=1
    if beathand(comphand, playerhand)==True: # Keep track of number of showdowns computer wins
        compwinsrevealed +=1
    print('Computer\'s Hand:') # Reveal computer's hand
    comphand.printhand()

def playermove(): # Player move procedure
    global playeramount
    global compamount
    global pot
    global bet
    global potprob
    global Xdata
    global ydata
    global playeraction
    global totalplayerbet
    move = input('Choose - fold, call, or raise: ')
    while move not in ['fold','call','raise']:
        move = input('Choose - fold, call, or raise: ')
    if move == 'fold':
        playeraction = 'fold'
        potprob = (pot-totalplayerbet)/(pot+bet)
        compamount += pot
        pot = 0
        bet = 0
        Xdata.append([potprob])
        ydata.append(1)
    elif move == 'call':
        playeraction = 'call'
        potprob = (pot-totalplayerbet)/(pot+bet)
        playeramount -= bet
        totalplayerbet +=bet
        pot += bet
        bet = 0
        Xdata.append([potprob])
        ydata.append(0)
    elif move == 'raise':
        playeraction = 'raise'
        if compamount <= 0:
            print('Computer doesn\'t have enough. Call.')
            amount = 0
        else:
            amount = int(input('Amount = $'))
            while amount > playeramount:
                amount = int(input('You don\'t have enough. Amount = $'))
        potprob = (pot-totalplayerbet)/(pot+bet+amount)
        playeramount -= bet
        totalplayerbet += bet
        pot += bet
        bet = amount
        playeramount -=amount
        totalplayerbet += amount
        pot +=amount
        Xdata.append([potprob])
        ydata.append(0)
    if len(Xdata) > memory: # Computer model built on last specified number of player moves (memory, default 100)
        Xdata.pop(0)
        ydata.pop(0)
    printamounts()

def compfold(): # Procedure for computer folding
    global playeramount
    global pot
    global bet
    playeramount +=pot
    pot =0
    bet = 0
    print('Computer folds')

def compcall(): # Procedure for computer calling
    global compamount
    global pot
    global bet
    global totalcompbet
    totalcompbet+=1
    compamount -= bet
    pot += bet
    bet = 0
    print('Computer calls')

def compraise(amount): # Procedure for computer raising
    global compamount
    global pot
    global bet
    global totalcompbet
    totalcompbet += 1
    compamount -= bet
    pot += bet
    bet = amount
    compamount -= amount
    totalcompbet += amount
    pot += amount
    print('Computer raises $'+str(amount))

# Sensible probability of folding, which is a logistic function of the difference between probability of being beat and
# pot probability threshold (this difference is equivalent to the expected amount lost normalized by pot size).
# This normalization helps prevent folding when little is on the table or not folding when a lot is on the table.
def probfold(potprob,handprob):
    return 1/(1+e**(-1*w*(handprob-potprob)))

def probplayerfold(potprob): # calculates player probability of folding
    if 0 in ydata and 1 in ydata:
        model = LogisticRegression(solver='liblinear')
        model.fit(Xdata, ydata)
        return model.predict_proba([[potprob]])[0][1]
    elif 0 in ydata:
        return 0.05
    elif 1 in ydata:
        return 0.95
    else:
        return 0.5

def estimateopp(potprob):
    global k
    global c
    pfold = probplayerfold(potprob)  # player's predicted probability of folding given current pot probability
    pbeatprior = playerprob(compdeck,comphand)
    if playeraction != 'Fold': # Bayes Theorem calculates probability given player action
        if playeraction is None:
            pbeatposterior = pbeatprior
        else:
            pbeatpotposterior = (1+pfold)/2
            # Player's probability of beating the computer is updated via Beta function
            pbeatposterior = 1-beta.cdf(1-pbeatprior,k*pbeatpotposterior,k*(1-pbeatpotposterior))
            pbeatposterior = c*pbeatposterior + (1-c)*pbeatprior
        return (pbeatposterior,pfold)
    else:
        return (potprob,0)

def compmove():
    playerprobs = estimateopp(potprob)
    compwinprob = playerprobs[0]*playerprobs[1]+(1-playerprobs[0])
    foldfreq = probfold(potprob, playerprobs[0])
    if comphandsrevealed != 0:  # The higher % of showdowns computer wins, the less likely bluffs will be called
        x = compwinsrevealed / comphandsrevealed
    else:
        x = 0.5
    raisefreq = 1 / (1 + e ** (-1 * (x - 0.75)))
    def foldorcall():
        if random() < foldfreq:
            compfold()
            printamounts()
            return 'fold'
        else:
            compcall()
            printamounts()
            return 'call'
    if compwinprob > (1-potprob): # If odds of winning or player folding is higher than pot odds, computer may raise
        if compamount >=10 and playeramount > 0:
            # If odds are in computer's favor, computer has a chance of raising depending on a random number
            if (pot - totalcompbet) / (pot + bet + 5) > playerprobs[0] and random() < raisefreq:
                if playeramount < 5:
                    compraise(playeramount)
                else:
                    compraise(5)
                printamounts()
                return 'raise'
            # But if hand is particularly good, computer will raise anyways
            elif (pot - totalcompbet) / (pot + bet + 10)/ (1 - compwinprob ) > 6 and\
                    (pot - totalcompbet) / (pot + bet + 10) > playerprobs[0]:
                # Computer raise restricted to 10 to prevent player from folding early
                raisefreq = compwinprob/(1+e**(-0.1*(compamount-compthreshold))) # Less likely to raise if less money
                if random() < raisefreq:
                    if playeramount < 10:
                        compraise(playeramount)
                    else:
                        compraise(10)
                    printamounts()
                    return 'raise'
                else:
                    if lastmoves[1] == 'call':# If player calls, computer will call since it doesn't lose anything
                        compcall()
                        printamounts()
                        return 'call'
                    else:
                        if playeraction is None:  # If the computer goes first, there is nothing saved by folding.
                            compcall()
                            printamounts()
                            return 'call'
                        else:
                            return foldorcall()
            # Still fairly good hand, but smaller raise
            elif (pot - totalcompbet) / (pot + bet + 5)/ (1 - compwinprob ) > 2 and\
                    (pot - totalcompbet) / (pot + bet + 5) > playerprobs[0]:
                # Computer raise restricted to 5 for hands that are not that great
                raisefreq = compwinprob/(1+e**(-0.1*(compamount-compthreshold)))
                if random() < raisefreq:
                    if playeramount < 5:
                        compraise(playeramount)
                    else:
                        compraise(5)
                    printamounts()
                    return 'raise'
                else:
                    if lastmoves[1] == 'call':# If player calls, computer will call since it doesn't lose anything
                        compcall()
                        printamounts()
                        return 'call'
                    else:
                        if playeraction is None:  # If the computer goes first, there is nothing saved by folding.
                            compcall()
                            printamounts()
                            return 'call'
                        else:
                            return foldorcall()
            else: # If mediocre hand and not bluff, there is a sensible chance of folding based on pot odds
                if lastmoves[1] == 'call':# If player calls, computer will call since it doesn't lose anything
                    compcall()
                    printamounts()
                    return 'call'
                else:
                    if playeraction is None:  # If the computer goes first, there is nothing saved by folding.
                        compcall()
                        printamounts()
                        return 'call'
                    else:
                        return foldorcall()
        else: # Good hand but not much money, computer will call and let the player choose to raise
            compcall()
            printamounts()
            return 'call'
    else: # If player calls, computer will call since it doesn't lose anything
        if playeraction is None: # If the computer goes first, there is nothing saved by folding.
            compcall()
            printamounts()
            return 'call'
        else:
            if lastmoves[1]=='call': # If user calls, computer can call without loosing anything
                compcall()
                printamounts()
                return 'call'
            else: # If the computer's hand is not that bad and it has enough money, it can call or fold
                if (1 - compwinprob )/((pot - totalcompbet) / (pot + bet)) < 1.5 and\
                        compamount-compthreshold > bet:
                    return foldorcall()
                else: # Otherwise the computer folds
                    compfold()
                    printamounts()
                    return 'fold'

def printamounts(): # Print player, computer, and pot money
    print('You: $' + str(playeramount) + ', Computer: $' + str(compamount) + ', Pot: $' + str(pot) + '\n')

# Gameplay
if __name__ == '__main__':
    maindeck = deck() # Initialize deck
    discard = pile() # Initialize empty discard pile
    compdeck = deck() # Initialize computer's memorized deck
    threshold = 0.5 # Reasonable expectation of being beaten
    playeramount = 100 # Inital amounts
    compamount = 100
    pot = 0
    minbet = 5
    bet = 0
    totalplayerbet = 0
    totalcompbet = 0
    # For a bet to be sensible, the probability of losing must be less than this value
    potprob = 1  # defined as gain/(gain+loss)=(pot-total bet)/(pot + bet + raise), gain is worst case (fold)
    w = 5 # Controls width of sensible folding cumulative probability curve
    k = 2
    c = 1
    Xdata = [] # Stores pot probability
    ydata = [] # Stores associated player action (fold or no fold)
    memory = 100 # Number of most recent player moves to consider in logistic regression
    playeraction = None # Player's last action
    comphandsrevealed = 0 # Number of computer hands revealed
    compwinsrevealed = 0 # Number of computer hands revealed and won
    compthreshold = 25 # Threshold number of dollars before computer is less likely to raise
    first = 'player' # Who goes first in the round

    lastmoves = deque([], maxlen=2)
    maindeck.shuffle()
    print('Each player starts with $100. Minimum bet $5\n')
    while True: # New round procedure
        lastmoves.append('spaceholder')
        lastmoves.append('spaceholder')
        if maindeck.size >= 10:
            deal()
        else:
            maindeck = deck()
            discard = pile()
            compdeck = deck()
            maindeck.shuffle()
            deal()
            printamounts()
            if playeramount <= 0 or compamount <= 0: # If someone runs out of money upon minimum bet
                endround()
            if playeramount <= 0 or compamount <= 0: # If after comparing hands someone has no money, end game
                break
        if first != 'player':
            lastmoves.append(compmove())
            playeraction = None
            if lastmoves[1] == 'fold': # If computer folds and runs out of money, the game ends
                if compamount <= 0:
                    break
                else: # If computer folds and still has money, a new round begins
                    endround()
                    lastmoves.append('spaceholder')
                    lastmoves.append('spaceholder')
                    if maindeck.size >= 10:
                        deal()
                    else:
                        maindeck = deck()
                        discard = pile()
                        compdeck = deck()
                        maindeck.shuffle()
                        deal()
                        printamounts()
            if playeramount <= 0 or compamount <= 0: # If someone runs out of money upon minimum bet or raise
                endround()
            if playeramount <= 0 or compamount <= 0: # If after comparing hands someone has no money, end game
                break
        while True: # Betting rounds
            playermove()
            lastmoves.append(playeraction)
            if lastmoves[1] == 'fold' or (lastmoves[0] == 'call' and lastmoves[1] == 'call'):
                break
            if playeramount <= 0 or compamount <= 0:
                break
            lastmoves.append(compmove())
            if lastmoves[1] == 'fold' or (lastmoves[0] == 'call' and lastmoves[1] == 'call'):
                break
            if compamount <= 0:
                break
        if lastmoves[1] == 'fold' or (lastmoves[0] == 'call' and lastmoves[1] == 'call'):
            endround()
        elif playeramount <= 0:
            lastmoves.append(compmove())
            endround()
        elif compamount <= 0:
            playermove()
            lastmoves.append(playeraction)
            endround()
        if playeramount <= 0:
            break
        elif compamount <= 0:
            break
    if not lastmoves:
        pass
    elif lastmoves[1] == 'fold' or (lastmoves[0] == 'call' and lastmoves[1] == 'call'):
        endround()
    elif playeramount <= 0:
        lastmoves.append(compmove())
        endround()
    elif compamount <= 0:
        playermove()
        lastmoves.append(playeraction)
        endround()
    if playeramount <= 0:
        print('You Lose.')
    elif compamount <= 0:
        print('You Win!')
