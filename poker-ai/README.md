# Poker AI
*Skills: Python, Probability*

### Overview
This is a simple straight heads-up poker game. The player and computer are each dealt a 5 card hand, with no drawing. The algorithm uses card counting, combinatorics, probability, Bayes theorem, logistic regression, and heuristics.

The computer cannot 'see' the player's cards except if they are revealed at the end of a showdown. The computer card counts to determine the probability of the player having a better hand. At any stage in betting, the computer calculates the probability threshold for which the expectation value of money won is 0, then creates a default average cumulative probability curve for folding.

The player's cumulative probability of folding is generated using logistic regression on the last 100 player actions. By comparing the mean cumulative probability to the player's model, the computer determines if the player is cautious or aggressive, and estimates the probability the player is bluffing or will fold prematurely. Using Bayes theorem, the computer recalculates the probability that the player will be under the threshold probability. This is used to update the probability that the player will have a hand that beats the computer's hand. If the probability that the computer's hand is higher plus the probability that the player's hand is higher and the player folds is lower than the threshold, the computer may raise. The frequency of raising is determined by how good the computer's hand is and/or how many successful showdowns have occurred.

### Combinatorics
The Poker AI stores a copy of the deck, which is called the computer deck. By card counting, it removes the cards that it has drawn and the cards that have been revealed during showdowns. The probability of the player having a hand higher than each hand, is then recalculated with this reduced computer deck. The AI then makes betting decisions based on these probabilities.

The probability of each Poker hand is straightforward to determine analytically for a full deck, but for partial decks it becomes extremely difficult, especially when one must consider the ranking based on the high card. A consistent way of calculating the probability is by actually iterating through combinations, (combined with some theoretical simplifications). These methods are summarized below.

__Straight Flush__\
<sup>5</sup>&#9824;  <sup>6</sup>&#9824;  <sup>7</sup>&#9824;  <sup>8</sup>&#9824;  <sup>9</sup>&#9824;\
For each suit and each value (not including 2 and 3 since they cannot be the high card in a straight), if the card is in the deck, the count is 1 if the card and the 4 preceeding cards are in the deck, and zero otherwise. 

__Flush__\
<sup>2</sup>&#9825;  <sup>K</sup>&#9825;  <sup>4</sup>&#9825;  <sup>7</sup>&#9825;  <sup>9</sup>&#9825;\
For each suit and each value (excluding 2-5, since they cannot be the high card of a flush), if the card is in the deck, the number *n* of cards of the same suit below the high card value is calculated, then the combinations are C<sup>*n*</sup><sub>4</sub>. Finally, the number of associated straight flushes (calculated above) must be subtracted.

__Straight__\
<sup>3</sup>&#9824;  <sup>4</sup>&#9825;  <sup>5</sup>&#x25CA;  <sup>6</sup>&#9825;  <sup>7</sup>&#9827;\
For each suit and each value (not including 2 and 3 since they cannot be the high card in a straight), if the card is in the deck, the count is zero if there are not at least 1 of the five values required. Otherwise, the number of cards of each required value (high card's value and the 4 preceeding numbers) are multiplied together to give the number of combinations. Then the number of associated straight flushes is subtracted once again.

__No Pair__\
<sup>2</sup>&#9824;  <sup>4</sup>&#9825;  <sup>8</sup>&#9824;  <sup>Q</sup>&#9825;  <sup>J</sup>&#9827;\
For each suit and each value (excluding 2-5 since they cannot be the high card in no pair), if the card is in the deck, the number of each value lower than the high card is counted. The total combinations is the sum of the products of these counts for every combination of 4 cards out of the available cards lower than the high card. Then the combinations of straight, flush, and straight flush are subtracted.

__Full House__\
<sup>J</sup>&#9824;  <sup>J</sup>&#9825;  <sup>J</sup>&#9827;  <sup>5</sup>&#9825;  <sup>5</sup>&#9827;\
For each suit and each value, if the card is in the deck and there are at least 2 other cards of the same value but a lower suit, then the combinations of all posible pairs (C<sup>*n*</sup><sub>2</sub> where *n* is the number of cards with the same value) for all other values are summed. This is multiplied by the combinations of triplets (C<sup>*n*</sup><sub>2</sub> where *n* is the number of cards with the same value as the high card but a lower suit).

__4 of a Kind__\
<sup>Q</sup>&#9824;  <sup>Q</sup>&#9825;  <sup>Q</sup>&#9827;  <sup>Q</sup>&#x25CA;  <sup>2</sup>&#9827;\
For spades only (since the high card in a 4 of a kind must be a spade) for each value, if all 4 suits are in the deck the count is 1, otherwise it is 0.

__3 of a Kind__\
<sup>7</sup>&#9825; <sup>7</sup>&#9824; <sup>7</sup>&#9827;  <sup>A</sup>&#x25CA;  <sup>2</sup>&#9827;\
For each suit and value, if the card is in the deck and there are at least 2 other cards of the same value but lower suit, the combinations are calculated as C<sup>*n*</sup><sub>2</sub>C<sup>*m*</sup><sub>2</sub> where *n* is the number of cards of the high value with lower suit that the high card, and *m* is the number of cards in the deck minus 3. Then the number of combinations of 4 of a kind and full house are subtracted.

__2 Pair__\
<sup>5</sup>&#9824; <sup>5</sup>&#9827;  <sup>A</sup>&#x25CA; <sup>A</sup>&#9825;  <sup>K</sup>&#9827;\
For each suit and value, if the card is in the deck and there is at least 1 other card of the same value but lower suit, the combinations are calculated as C<sup>*n*</sup><sub>1</sub> (where *n* is the number of cards of the high value with lower suit that the high card), times the sum of the product of C<sup>*m*</sup><sub>2</sub> (where *m* is the number of cards with the same value as the second pair) and the number of cards that have a different value than the pairs (the sum is over values lower than the high card).

__1 Pair__\
<sup>4</sup>&#9827;  <sup>4</sup>&#x25CA; <sup>3</sup>&#9825;  <sup>Q</sup>&#9827; <sup>5</sup>&#9824; \
For each suit and value, if the card is in the deck and there is at least 1 other card of the same value but lower suit, the combinations are C<sup>*n*</sup><sub>1</sub> (where *n* is the number of cards of the high value with lower suit that the high card) times the sum of the product of the number of cards of each of 3 values, for all combinations of 3 values that are not equal to the value of the pair.


### Probability of Losing Hand
Once the combinations of all hands has been determined, the probability is determined by dividing by C<sup>*n*</sup><sub>5</sub> where *n* is the total number of cards in the deck.

The probabilities of all the different hands are arranged in order. Then the cumulative sum is used to calculated the probability of the user having a higher or lower hand than the computer. The probability of having a losing hand will be denoted as *p<sub>lose</sub>*. Note that this is calculated assuming nothing is known about the opponent's hand, in other words the probability density distribution is uniform for the opponent.

### Pot Probability
Another important probability is the pot probability (related to pot odds), *p<sub>pot</sub>*. The pot probability is defined as *gain / (gain+loss)*, which, as a conservative estimate, is calculated as *(pot - total previous bet) / (pot + current bet + current raise)*. This represents the reqired probability of having a losing hand to break even on average. The higher the pot probability, the higher probability of losing the player can tolerate. For a bet to be sensible, the probability of having a losing hand and unsuccessful bluff must be less than the pot probability.

### Probability of Folding
The following are heuristic approximation models of player behavior. They are not necessarily theoretically rigorously provable, but are useful to describe the behavior generally. Note that the models are for folding vs. not folding. Calling and raising are not distinguished because they are accounted for in the pot probability (raising will lower the pot probability compared to just calling).

The probability of folding *p<sub>fold</sub>* is modeled as a logistic function. The computer will be sensible, having an initial probabilty of folding of 1/(1+e<sup>-*w*(*p<sub>lose</sub>* - *p<sub>pot</sub>*)</sup>), where *w* is a constant. 

The player, however may not be sensible. To determine how reckless or conservative the user is, logistic regression is performed on the player's most recent 100 moves (or less if the game has not progressed that far). The x values are the *p<sub>pot</sub>* and the y values are 1 (fold) or 0 (not fold). This will approximate the user's probability of folding on average, *f<sub>user</sub>*(*p<sub>pot</sub>*). On average the probability of having a losing hand is 0.5. If the inflection of the logistic regression curve is less than 0.5, the player is agressive. If the inflection is much greater than 0.5, the player is conservative.

By comparing the logistic regression results with the sensible logistic function of *f<sub>0</sub>*(*p<sub>pot</sub>*)=1/(1+e<sup>-*w*(0.5 - *p<sub>pot</sub>*)</sup>), the probability of bluffing and over-cautious folding can be estimated.

<img src="images/PokerFig1.png" width="700">

For the aggressive player, the probability of folding when it is appropriate to fold (when the player has a bad hand) is approximately *p<sub>appropriate</sub>* = *f<sub>user</sub>*, assuming that the aggressive player will not be overcautious and fold with a winning hand (*p<sub>cautious</sub>* = 0). The probability of the player bluffing (not folding when the player has a bad hand) is *p<sub>bluff</sub>* = *f<sub>0</sub>*-*f<sub>user</sub>*. And the probability of not folding when the player has a hand that is likely to beat the computer is *p<sub>beat</sub> = 1-*f<sub>user</sub>*.

<img src="images/PokerFig2.png" width="700">

For the cautious player, the probability of folding when it is appropriate to fold is *p<sub>appropriate</sub>* = *f<sub>0</sub>*. The probability of folding when the player has a good hand is *p<sub>cautious</sub>* =*f<sub>user</sub>*-*f<sub>0</sub>*. And the probability of not folding when the player has a good hand is *p<sub>no fold</sub>*=*p<sub>beat</sub>* assuming the player is too cautious to ever bluff (*p<sub>bluff</sub>* = 0).

### Bayes' Theorem
The goal of calculating the probability of folding is to use the player action combined with the pot probability to update the probability that the player will have a hand that beats the computer. Bayes' Theorem can be used to achieve this.

As mentioned earlier, the sensible betting means having the pot probability be no smaller than the probability of losing (*p<sub>lose</sub>*). The limit of sensible behavior would be described by *p<sub>pot</sub>* = *p<sub>lose</sub>* = 1-*p<sub>win</sub>*. The prior probability for the player winning, given the pot odds, is therefore *p<sub>win,prior</sub>* = 1-*p<sub>pot</sub>*. (Once again, *p<sub>win</sub>* refers to the probability of winning assuming a uniform distribution for the opponent).

For the case where the player does not fold (which is the only case where the computer would need to do any calculations) the posterior probability of the player winning *p<sub>win,post</sub>* is calculated according to Bayes' Theorem as\
((1-*p<sub>pot</sub>*) x *p<sub>beat</sub>*)/((1-*p<sub>pot</sub>*) x *p<sub>beat</sub>*+*p<sub>pot</sub>* x *p<sub>bluff</sub>*)


<img src="images/PokerFig3.png" width="500">







