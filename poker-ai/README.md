# Poker AI
*Skills: Python, Probability*

### Overview
This is a simple straight heads-up poker game. The player and computer are each dealt a 5 card hand, with no drawing. The algorithm uses card counting, combinatorics, probability, logistic regression, and heuristics.

The computer cannot 'see' the player's cards except if they are revealed at the end of a showdown. The computer card counts to determine the probability of the player having a better hand. At any stage in betting, the computer calculates the probability threshold for which the expectation value of money won is 0, then creates a default average cumulative probability curve for folding.

The player's cumulative probability of folding is generated using logistic regression on the last 100 player actions. By comparing the mean cumulative probability to the player's model, the computer determines if the player is cautious or aggressive, and estimates the probability the player is bluffing or will fold prematurely. Using Bayes theorem, the computer recalculates the general probability that the player will win (assuming uniform distribution of the computer's hand). This is used to update the probability that the player will have a hand that beats the computer's hand. If the probability that the computer's hand is higher plus the probability that the player's hand is higher and the player folds is lower than the threshold, the computer may raise. The frequency of raising is determined by how good the computer's hand is and/or how many successful showdowns have occurred.

*Prerequisite Libraries: sklearn, scipy*

### Combinatorics
The Poker AI stores a copy of the deck, which is called the computer deck. By card counting, it removes the cards that it has drawn and the cards that have been revealed during showdowns. The probability of the player having a hand higher than each hand, is then recalculated with this reduced computer deck. The AI then makes betting decisions based on these probabilities.

The probability of each Poker hand is straightforward to determine analytically for a full deck, but for partial decks it becomes extremely difficult, especially when one must consider the ranking based on the high card. A consistent way of calculating the probability is by actually iterating through combinations, (combined with some theoretical simplifications). These methods are summarized below.

__Straight Flush__\
<sup>5</sup>&#9824;  <sup>6</sup>&#9824;  <sup>7</sup>&#9824;  <sup>8</sup>&#9824;  <sup>9</sup>&#9824;\
For each suit and each value (not including 2 and 3 since they cannot be the high card in a straight), if the card is in the deck, the count is 1 if the 4 preceding cards are also in the deck, and zero otherwise. 

__Flush__\
<sup>2</sup>&#9825;  <sup>K</sup>&#9825;  <sup>4</sup>&#9825;  <sup>7</sup>&#9825;  <sup>9</sup>&#9825;\
For each suit and each value (excluding 2-5, since they cannot be the high card of a flush), if the card is in the deck, the number *n* of cards of the same suit below the high card value is calculated, then the combinations are C<sup>*n*</sup><sub>4</sub>. Finally, the number of associated straight flushes (calculated above) must be subtracted.

__Straight__\
<sup>3</sup>&#9824;  <sup>4</sup>&#9825;  <sup>5</sup>&#x25CA;  <sup>6</sup>&#9825;  <sup>7</sup>&#9827;\
For each suit and each value (not including 2 and 3 since they cannot be the high card in a straight), if the card is in the deck, the count is zero if there are not at least 1 of the five values required. Otherwise, the number of cards of each required value (high card's value and the 4 preceding numbers) are multiplied together to give the number of combinations. Then the number of associated straight flushes is subtracted once again.

__No Pair__\
<sup>2</sup>&#9824;  <sup>4</sup>&#9825;  <sup>8</sup>&#9824;  <sup>Q</sup>&#9825;  <sup>J</sup>&#9827;\
For each suit and each value (excluding 2-5 since they cannot be the high card in no pair), if the card is in the deck, the number of each value lower than the high card is counted. The total combinations is the sum of the products of these counts for every combination of 4 cards out of the available cards lower than the high card. Then the combinations of straight, flush, and straight flush are subtracted.

__Full House__\
<sup>J</sup>&#9824;  <sup>J</sup>&#9825;  <sup>J</sup>&#9827;  <sup>5</sup>&#9825;  <sup>5</sup>&#9827;\
For each suit and each value, if the card is in the deck and there are at least 2 other cards of the same value but a lower suit, then the combinations of all possible pairs (C<sup>*n*</sup><sub>2</sub> where *n* is the number of cards with the same value) for all other values are summed. This is multiplied by the combinations of triplets (C<sup>*m*</sup><sub>2</sub> where *m* is the number of cards with the same value as the high card but a lower suit).

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


### Probability of a Losing Hand
Once the combinations of all hands have been determined, the probability is determined by dividing by C<sup>*n*</sup><sub>5</sub> where *n* is the total number of cards in the deck.

The probabilities of all the different hands are arranged in order. Then the cumulative sum (which will be referred to as the rank of the hand) is the probability of the user having a lower hand than the computer. The probability of the user having a winning hand will be denoted as *p<sub>win</sub>* or *p<sub>complose</sub>*. Note that this is calculated assuming nothing is known about the opponent's hand, in other words the probability density distribution is uniform for the opponent (the opponent is equally likely to have any hand).

### Pot Probability
Another important probability is the pot probability (related to pot odds), *p<sub>pot</sub>*. The pot probability is defined as\
*gain / (gain+loss)*, which, as a conservative estimate, is calculated as *(pot - total previous bet) / (pot + current bet + current raise)*. This represents the required probability of having a losing hand to break even on average. The higher the pot probability, the higher probability of losing the player can tolerate. For a bet to be sensible, the probability of having a losing hand (and unsuccessful bluff if applicable) must be less than the pot probability.

### Probability of Folding
The following are heuristic approximation models of player behavior. They are not necessarily theoretically rigorously provable, but are useful to describe the behavior generally. Note that the models are for folding vs. not folding. Calling and raising are not distinguished because they are accounted for in the pot probability (raising will lower the pot probability compared to just calling).

The probability of folding *p<sub>fold</sub>* is modeled as a logistic function. The computer will be sensible, having an initial probability of folding of *p<sub>compfold</sub>*=1/(1+e<sup>-*w*(*p<sub>complose</sub>* - *p<sub>pot</sub>*)</sup>), where *w* is a constant. 

The player, however may not be sensible. To determine how reckless or conservative the user is, logistic regression is performed on the player's most recent 100 moves (or less if the game has not progressed that far). The x values are the *p<sub>pot</sub>* and the y values are 1 (fold) or 0 (not fold). This will approximate the user's probability of folding on average, *f<sub>user</sub>*(*p<sub>pot</sub>*). On average the probability of having a losing hand is 0.5. If the inflection of the logistic regression curve is less than 0.5, the player is aggressive. If the inflection is much greater than 0.5, the player is conservative.

<img src="images/PokerFig1.png" width="700">

### Conditional Probability
The goal of calculating the probability of folding is to use the player action combined with the pot probability to update the probability that the player will have a hand that beats the computer. The desired value is *p*( win | no fold ) for the player, assuming a uniform distribution for the computer.

With the available information, it is easier to directly estimate *p*( win | no fold ) rather than try to use Bayes' Theorem, which would require more terms that are not easily derived or estimated. The logistic regression equation is the overall frequency of folding given *p<sub>pot</sub>*. If the folding decision is completely random, but following the frequency in the regression equation, then it is independent of how good the player's hand is, and *p*( win ) = *p*( win | no fold ) = *p*( win | fold ) = 0.5 given no further information. Or perhaps if the player is sensible, the probability of a losing hand is somewhere less than *p<sub>pot</sub>*, on average it would be *p<sub>pot</sub>*/2, making *p*( win )=1-*p<sub>pot</sub>*/2. However, this would only be if the player is sensible. There is no obvious way of converting the logistic regression into a relationship between *p*( win ) and *p<sub>pot</sub>*. In any case this clearly is not helpful because it doesn't provide any information about the player's hand based on the player's action.

However, if instead we assume that the player's decision to fold or not fold is based on the player's hand rather than being just random, then the frequency can be interpreted as the threshold rank of the player's hand below which the player will fold. (The term "rank" here is used to describe the probability of having a lower hand from a uniform distribution of all possible hands. In other words it is the probability of the user winning, assuming nothing about the computer's hand).

Therefore, if the player folds, the player's hand must have been somewhere below the threshold *p<sub>fold</sub>*. Without additional information, it is assumed that in these regions the player's hand is uniformly distributed. Then, if the computer's hand is also uniformly distributed, the probability that the computer's hand is in the same region as the player's is simply *p<sub>fold</sub>*. Then the probability that the computer's hand is less than the player's hand is *p<sub>fold</sub>*/2 (either one is equally likely to be higher). This therefore is *p*( win | fold ). This value is not that useful, since the computer doesn't need to decide anything if the player folds.

<img src="images/PokerFig2.png" width="700">

If the player does not fold, the player's hand must be in the region above the threshold *p<sub>fold</sub>* (once again assuming uniform distribution). The probability that the computer's hand is in that same region is 1-*p<sub>fold</sub>*. And the probability of the computer's hand being lower in that region is (1-*p<sub>fold</sub>*)/2. The probability of the computer's hand being below the threshold is *p<sub>fold</sub>* and the probability of the computer's hand being below the player's hand in this case is 1. \
Then overall *p*( win | no fold ) = *p<sub>fold</sub>* x 1 + (1-*p<sub>fold</sub>*)/2 = (1+*p<sub>fold</sub>*)/2.

<img src="images/PokerFig3.png" width="700">

This result came with many approximations and assumptions, so it is not very certain. Instead of just assuming that the player will win if the *p*( win | no fold ) is greater than the probability of the computer's hand winning, the probability is calculated on a posterior distribution of the player's hands. The prior was a uniform distribution. Bayes' Theorem cannot really be used here to calculate the posterior because the conditional probabilities cannot be calculated (it would require calculating the probability of the above heuristic model being correct, which is not easily defined). Instead, a pseudo-posterior distribution will be assumed to be a beta distribution with a mean of *p*( win | no fold ). \
In other words Beta(*kp*( win | no fold ),*k*(1-*p*( win | no fold ))) where *k* is some constant that can be tuned. The constant represents the weight that the computer will put on the player's move given the player's history. The cumulative probability of the pseudo-posterior distribution is then used to determine the posterior probability of the player having the better hand, which will be called *p<sub>win,final</sub>*.

### Computer Behavior
The probability of the computer folding, after all the above calculations, is *p<sub>compfold</sub>*=1/(1+e<sup>-*w*(*p<sub>win,final</sub>* - *p<sub>pot</sub>*)</sup>). However, the computer will most likely not consider folding unless its odds are not good.

The computer can win if either it has the better hand or the player folds. This probability is *p<sub>compwin</sub>*=*p<sub>win,final</sub>* x *p<sub>fold</sub>* + (1-*p<sub>win,final</sub>*). So even if the player's hand is better, if the player is conservative and has a high chance of folding, the computer may raise. If the probability of losing (1-*p<sub>compwin</sub>*) is less than the pot probability, the computer considers raising. If (1-*p<sub>compwin</sub>*) is more than the pot probability by a certain amount, then the computer will always fold unless the player calls, then the computer will call, since it doesn't lose anything. If (1-*p<sub>compwin</sub>*) is close enough to the pot probability, the computer will decide whether to call or fold based on *p<sub>compfold</sub>*.

In the case where the computer considers raising, to prevent the computer from constantly raising, the raises are random, but occur according to a raise frequency calculated as 1/(1+e<sup>-(x-0.75)</sup>) where x is the fraction of revealed computer hands that beat the player's hand. If less than 75% of the showdowns ended with the computer winning, the computer is less likely to raise. This seems skewed, but cases where the opponent bluffs will stand out more in the player's mind, since people tend to emphasize negative attributes in their assessment of others (e.g. if someone lies 25% of the time, many would still consider that person a liar). This ensures that the computer does not bluff too much if it has a history of showdowns that ended unfavorably. This way the player will not be tempted to keep calling the computer's bluff.

The above behavior is overridden depending on the ratio of pot probability and (1-*p<sub>compwin</sub>*). If the ratio is greater than some threshold (6 is used in this program), then the computer will raise $10. If the ratio is greater than 2 and less than 6, the computer will raise $5. These raises occur with a different raise frequency, that is only limited by the amount of money the player and computer has left (the computer will keep raising until someone runs out of money).

In all cases, if the computer does not raise, it will decide whether to call or fold randomly based on the frequency *p<sub>compfold</sub>*. However, if the player calls, the computer will always call, since there is nothing to lose.

The default computer behavior may seem somewhat aggressive to some. The behavior can be tweaked by altering the various thresholds and constants described above.


