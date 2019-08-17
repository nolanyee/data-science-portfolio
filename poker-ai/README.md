# Poker AI
*Skills: Python, Probability*

### Overview
This is a simple straight heads-up poker game. The player and computer are each dealt a 5 card hand, with no drawing. The algorithm uses card counting, combinatorics, probability, Bayes theorem, logistic regression, and heuristics.

The computer cannot 'see' the player's cards except if they are revealed at the end of a showdown. The computer card counts to determine the probability of the player having a better hand. At any stage in betting, the computer calculates the probability threshold for which the expectation value of money won is 0, then creates a default average cumulative probability curve for folding.

The player's cumulative probability of folding is generated using logistic regression on the last 100 player actions. By comparing the mean cumulative probability to the player's model, the computer determines if the player is cautious or aggressive, and estimates the probability the player is bluffing or will fold prematurely. Using Bayes theorem, the computer recalculates the probability that the player will be under the threshold probability. This is used to update the probability that the player will have a hand that beats the computer's hand. If the probability that the computer's hand is higher plus the probability that the player's hand is higher and the player folds is lower than the threshold, the computer may raise. The frequency of raising is determined by how good the computer's hand is and/or how many successful showdowns have occurred.

### Combinatorics
The Poker AI stores a copy of the deck, which is called the computer deck. By card counting, it removes the cards that it has drawn and the cards that have been revealed during showdowns. The probability of the player having a hand higher than each hand, is then recalculated with this reduced computer deck. The AI then makes betting decisions based on these probabilities.

The probability of each Poker hand is straight foward to determine analytically for a full deck, but for partial decks it becomes extremely difficult, especially when one must consider the ranking based on the high card. A consistent way of calculating the probability is by actually iterating through combinations, (combined with some theoretical simplifications). These methods are summarized below.

__Straight Flush__\
For each suit and each value (not including 2 and 3 since they cannot be the high card in a straight) the count is 1 if the card and the 4 preceeding cards are in the deck, and zero otherwise. 

__Flush__\
For each suit and each value (excluding 2-5, since they cannot be the high card of a flush) the number *n* of cards of the same suit below the high card value is calculated, then the combinations are C<sup>*n*</sup><sub>4</sub>. Finally, the number of associated straight flushes (calculated above) must be subtracted.

__Straight__\
For each suit and each value (not including 2 and 3 since they cannot be the high card in a straight) the count is zero if there are not at least 1 of the five values required. Otherwise, the number of cards of each required value (high card's value and the 4 preceeding numbers) are multiplied together to give the number of combinations. Then the number of associated straight flushes is subtracted once again.

__No Pair__\
For each suit and each value (excluding 2-5 since they cannot be the high card in no pair) the number of each value lower than the high card is counted. The total combinations is the sum of the products of these counts for every combination of 4 cards out of the available cards lower than the high card. Then the combinations of straight, flush, and straight flush are subtracted.

__Full House__\





