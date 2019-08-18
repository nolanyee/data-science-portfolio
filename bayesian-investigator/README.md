# Bayesian Network Investigator
*Skills: Python, Probability, Algorithms, Gradient Descent*

### Overview
This prototype application is intended to facilitate construction of Bayesian networks and serve as a simpler version of a Bayesian network in cases where the joint probabilities for each node are mostly unknown and there is not enough data to learn them. It is also able to show paths and nodes in the network that are suspect when contradictory evidence is given.

<img src="images/BayesFig7.png" width="700">

### Motivation
Often times in settings such as an analytical laboratory or manufacturing environment troubleshooting complex issues is required. Troubleshooting is aided by the construction of diagrams. Fishbone diagrams are popular, but in complex cases they do not adequately represent the causal connections between different events, and they rely on the user's reasoning abilities to deduce causality. Causal diagrams based on graphs are much more flexible. Such graphs can be analyzed by constructing a corresponding Bayesian network. However, these networks require the input of many conditional probability tables. Often these probabilities are not known and there is not enough data collected to learn them, as troubleshooting usually seeks to solve the problem with a minimum number of experiments. It is desirable to have a simpler version of a Bayesian network that has a limited number on node types with defined conditional probability patterns that the user can choose from. In addition, since even the structure of the networks may just be hypothetical, it is beneficial to have software that can hint at which connections might be incorrect in the case of contradictory evidence.

### Theoretical Background

__Notation__

*p*(*T*) = probability that node of interest is T (true)\
*p*(*e*) = probability of the evidence (nodes set by the user)\
*p*(*T* | *e*) = probability that the node of interest is T given the evidence\
*p*(*e* , *T*) = probability that the node of interest is T and the evidence is correct\
*p*(*T<sub>i</sub>*) = probability that the *i*<sup>th</sup> parent node is T\
*w<sub>i</sub>* =  weight of parent node\
*P<sub>i</sub>* = state (T or F) of *i*<sup>th</sup> parent node
 
__Simplifications__
1. Binary nodes only (T or F)
2. Only five types of nodes
3. 	The effect of any parent node *i* is related to the weighted probability that the parent is T,
either *p*(*T<sub>i</sub>*)*w<sub>i</sub>* or 1-*p*(*T<sub>i</sub>*)*w<sub>i</sub>*.

__Consequences of the Simplifications__\
Let *p*(*T*) be the probability that the node of interest is true. The definition of the node types is such that the marginal probability is a polynomial of the products of weights and probabilities that parents are T\
*p*(*T*)=*f*(*p*(*T<sub>1</sub>*)*w<sub>1</sub>*,...*p*(*T<sub>n</sub>*)*w<sub>n</sub>*)\
and the conditional probability of a node being true (given the state of the parents *P<sub>i</sub>*) is a function of the weights\
*p*(*T* | *P<sub>1</sub>* ...*P<sub>n</sub>* )=*f*(*w<sub>1</sub>*,...,*w<sub>n</sub>* )\
This makes it easier to calculate the probabilities and it means that a network may be constructed without entering the full joint distribution information at each node, which is not always easily derived. 

__Main Node__

Main nodes have a probability of being T if at least 1 parent is T. If all parents F, probability of T is 0.

If the parents are independent, the probability is dependent on the weighted probability of the parents *p*(*T<sub>i</sub>*)*w<sub>i</sub>* as the sum of combinations of the different parents containing from 1 to *n* parents.

<img src="images/BayesEq1.png" width="500">

using the inclusion-exclusion principle.

<img src="images/BayesEq2.png" width="250">
                                         
The conditional probability if all the parents are false is 0, and if at least one of the parents is true the conditional probability is

__Interaction Node__

Interaction nodes have a probability of being T if all parents are T. If any parent is F, the probability of T is 0.
If the parents are independent, the probability is dependent on *p*(*T<sub>i</sub>*)*w<sub>i</sub>* as

<img src="images/BayesEq3.png" width="150">

If any parent is false, the conditional probability is 0, if all parents are true, the conditional probability is

<img src="images/BayesEq4.png" width="170">

__Exclusion Node__

Exclusion nodes have a probability of being T if 1 parent is T, otherwise the probability is

<img src="images/BayesEq5.png" width="500">

using the inclusion-exclusion principle.

If all parents are false the conditional probability is 0. Otherwise, it is

<img src="images/BayesEq6.png" width="250">

If the all the weights are not 1, then this node is partially exclusive, meaning if more than one is true, the probability will decrease, but not all the way down to 0. If all the weights are 1, then

<img src="images/BayesEq7.png" width="200">

__Inverted Node__

Inverse nodes have probability 1 of being T if at least 1 parent is F, and otherwise

<img src="images/BayesEq8.png" width="160">

The conditional probability is 1 if at least one parent is F, otherwise

<img src="images/BayesEq9.png" width="180">

__Inverted Interaction Node__

Inverse interaction nodes have probability 1 of being T if all parents are F, and otherwise

<img src="images/BayesEq10.png" width="500">

using the inclusion exclusion principle.

The conditional probability is 1 if all parents are F, otherwise it is

<img src="images/BayesEq11.png" width="200">

__Common Ancestors__

The above equations apply only if the parents are completely independent. It is possible for some parents to be dependent if they share a common ancestor. 

Note that all the above expressions expand to a linear combination of products of *p*(*T<sub>i</sub>*)*w<sub>i</sub>* and 1. This means all probabilities can be expressed as a linear combinations of probabilities that different combinations of parents are T. 

In the case of shared ancestors, if the above expressions are used, when fully expanded in terms of roots (parentless nodes or Eves, as they are referred to in the code, to distinguish from the root Tk widget) there will be terms with parent probability and weight terms that are raised to some power greater than one, which represents double counting of those terms (treating them as independent when they are actually the same). Therefore the power of all terms in the expanded expressions must be reduced to 1. The resulting calculation is the marginal probability for a single node.

Note that the expressions will contain weights corresponding to itself (the effects of its parents on itself) and the weights of all its ancestors. Therefore the list of weights in any child node’s equation is always longer than that of its ancestors. So the order of inheritance is just the nodes sorted by the number of different weights in the equations.

__Bayesian Inference__

For inference, the network must be able to update based on evidence. This can be done using Bayes’ Theorem.

<img src="images/BayesEq12.png" width="150">

*p*(*e*) is obtained by unsetting all the evidence (calculating the prior network) and then setting the evidence one node at a time in order of inheritance (meaning children always go after parents). Before each node is set, the probability is collected and after all nodes have been set the product of all probabilities is taken. Then any exponents are removed to prevent any common ancestor effects which may occur if evidence nodes are siblings or cousins. *p*(*e* , *T*) is calculated the same way except the node of interest is included in the calculation. This process is repeated for all the non-evidence nodes. Memoization is used to prevent repeat calculations.

__Investigating Contradictory Evidence__

Since the joint distributions contain many simplifications (cases where probabilities are 0 or 1) there can be amplification of problems when contradictory evidence is entered. The calculation of conditional probability of a node being true given evidence may often result in division by 0. Since the intended use of the program is to explore different possible network structures, it is likely that contradictions will occur.

As an alternative, probabilities can propagated forward from the evidence (i.e. calculated from parents) until another evidence node is reached. The evidence in that node can be removed and if the calculated probability of that node differs from the evidence by some threshold, then the path from the two nodes can be flagged as containing a connection that perhaps is not true. In this way, this type of network not only gives information about each node, but also flags potentially erroneous connection paths. Backwards probabilities may be derived by adjusting priors of parentless nodes using gradient descent, before contradictions are evaluated.

In addition, gradient descent on the weights can determine which weights need to be increased or decreased. If the weights are not restricted to between 0 and 1, negative weights can indicate that the type of node should be switched from Main to Inverted or vice versa. Weights greater than 1 indicate that another parent should be added (typically called ‘other’ representing an unknown cause).

__Auxiliary Nodes__

If a node is set as auxiliary, the weights of edges between the node and its parents are set to 1 and the symbols for the weights in the associated equations are replaced by 1. This results in no updating of the weight during gradient descent. Typically modifying nodes can be set as auxiliary to significantly decrease calculation times because the symbol does not need to be tracked throughout the calculation. There is no danger of double counting the weight because 1n=1 for any n. Such nodes are always expected to have a direct link with the parents (weights are all 1). For example an inverted node that represents the negation of a parent will always have a direct link to the parent. Likewise exclusion, interaction, and inverted interaction nodes typically have direct links to parents. If only Bayesian mode will be used, then all nodes with weights of 1 on the edges from their parents can be set as auxiliary to achieve minimum calculation time.

__Graphical User Interface__

The program uses a Tk based GUI. Instructions for creating networks are as follows:

Right-Click = Create node\
Left-Click Hold = Drag node\
Shift-Left-Click = Create edge connecting parent to child node\
Alt-Left-Click = Delete edge (same order as to create edge)\
Click on + to expand node, set evidence, select node type, set node as auxiliary, or delete node\
Control-b= Set prior (enter node name and prior value in Python window)\
Control-s = Save as text file (enter path and filename in Python window)\
Control-o = Load text file (enter path and filename in Python window)\
Control-h = Help (Displayed in Python window)\
Control-p = profile the update() function (for developers, may change to another function as needed)\
Set weights by typing in the entry widget in the middle of the edge (use numerical values between 0 and 1).

The probability of the node being True is displayed below the name of the node. This label is colored as follows:\
Black = Main\
Blue = Interaction\
Green = Exclusion\
Red = Inverted\
Magenta = Inverted Interaction

If a node is set as evidence (by checking the True or False box) the label is bold.

In investigation mode, if the node is a contradictory descendent of other evidence nodes, the label will have a sunken border. The edge colors represent:

Darker = Edge does not need to be changed much (small change after gradient descent)\
Bright = Edge must be changed (large change after gradient descent)\
Red = Weight must be decreased or edge deleted (decrease after gradient decent)\
Green = Weight must be increased (Increase after gradient descent)\
Blue = Another parent must be added or edge must be deleted (greater than 1 after gradient descent)\
Yellow = Node type needs to be inverted (main to inverted or vice versa) or edge must be deleted (less than 0 after gradient descent, rare)
 
By default, in Investigation mode, the probability of roots is calculated based only on the nodes closest to the roots, and the line colors are based on weight optimization for only the nodes marked as contradictory evidence. Also gradients are calculated for each node with all other evidence nodes fixed (as 0 or 1 it False or True, respectively). 

If ‘Use All Evidence’ is selected, all evidence nodes are used to calculate root probabilities and line colors, and the gradients keep the terms in the equation corresponding to evidence nodes instead of substituting their set values. The loss function is defined as the sum of squares of deviations for all evidence nodes.

The gradient descent for line weights is constrained to between 0 and 1 only if the ‘Constrained’ box is selected. Otherwise it is allowed to go below 0 (resulting in a yellow line) or above 1 (resulting in a blue line).

__Techniques__

Exclusion nodes most often are used as modifiers to enforce mutual exclusivity of different nodes. As a trivial example, if you know your acquaintance has a child named Elizabeth, and that she only has one child, then in the past she was pregnant with a girl.

<img src="images/BayesFig1.png" width="500">

Inversion nodes can also be used as modifiers.

<img src="images/BayesFig2.png" width="500">

Additional parent nodes, called ‘other’ nodes, can be used to allow for a node to be true even if the other parents are false.

<img src="images/BayesFig3.png" width="600">

__Examples__

Due to having only 5 different types of nodes. Not all Bayesian networks can be replicated with this application.
However, many simpler ones can be replicated. For example these two networks are equivalent

<img src="images/BayesFig4.png" width="700">

<img src="images/BayesFig5.png" width="700">

As a second example, the Asia network is translated as

<img src="images/BayesFig6.png" width="900">

<img src="images/BayesFig7.png" width="900">

<img src="images/BayesFig8.png" width="900">

<img src="images/BayesFig9.png" width="900">

__Bayesian Mode Example__

In this example, an extra peak in a particle size histogram is observed. Different possible causes are remedied. After being fixed if the problem persists, these nodes are set to False while the extra peak node is still True. For the nodes that did decrease the frequency of extra peak observations (but not completely eliminate them), they are set to True while the extra peak node is True (the observed effect after these causes were remedied (made False) demonstrated that these nodes were True at the time the ineffective nodes were tested). The state of the evidence after testing the nodes that made no difference is used to update the network. Once updated, the potential mechanisms of the observed problem are narrowed down.

<img src="images/BayesFig10.png" width="900">

<img src="images/BayesFig11.png" width="900">

<img src="images/BayesFig12.png" width="900">

__Investigation Mode Examples__

Under Bayesian mode updating this network would result in a contradictory evidence error.

<img src="images/BayesFig13.png" width="900">

Under Investigation mode, with ‘Use All Evidence’ unchecked the root is optimized to match the closest child. Since the evidence are not considered contradictory unless the probability of observing the evidence is less than 10% (this may be altered in the code).

<img src="images/BayesFig14.png" width="900">

If ‘Use All Evidence’ is checked, the root is optimized to reduce the total sum of squares from all evidence nodes. In this case, the result is the same. However, it also optimizes the weights based on all evidence nodes, even if they are not flagged as contradictory. This results in the following.

<img src="images/BayesFig15.png" width="900">

To match the evidence, the green lines indicate that the weight should be increased. The red lines indicate the weight should be decreased.

The next generic example shows the difference in behavior of Investigation mode for different types of nodes.
The ‘Use All Evidence’ is unchecked, root optimization is done for the closest evidence descendant only, which is node H, while treating other evidence as fixed. Since node A is fixed at 1, none of the roots have any effect on node H’s theoretical probability, which is always 1. Therefore the root probability is not changed. However, when ‘Use All Evidence’ is checked, the gradient descent is done to optimize the theoretical probability of both A and H simultaneously, and their probabilities are treated as variables instead of fixed values. Thus all the roots become 0, because if A were not 1, then the other roots must be 0 to ensure H is 0.  

<img src="images/BayesFig16.png" width="900">

If node F is changed to interaction and the evidence is changed, under constrained mode the line colors don’t change because weights are restricted to between 0 and 1. However, if not constrained, the paths related to the contradiction become blue. Recall that blue represents weights above 1. In this case, since all the roots are 0, the blue actually represents weights of positive infinity.  In this case it means that one or more of the blue edges must be deleted to resolve the contradiction, or an ‘other’ node must be added to a main node somewhere (node D).

<img src="images/BayesFig17.png" width="900">

If F is set as an exclusion node, the results are more interesting. If constrained, the three different results are observed. For cases where the weights are all balanced, the gradient starts out as 0. However, the gradient descent algorithm takes the first step in a random direction to move off a maximum or a saddle point. In this case it results in different edges being flagged for deletion. In order to make the exclusion node true, only one of the parents is allowed to be true. The link to the other one is marked red. However, since E and G are equivalent, either linkage could be valid, thus the random alternation. Rarely, the third case will occur, where gradient descent decreases both edges roughly equally. The edges from C to D to F are still black because no change in weight between 0 and 1 can make a probability of 0 into a 1.

<img src="images/BayesFig18.png" width="900">

If ‘constrained’ is unchecked, the results are a mix of all possible scenarios. The blue lines indicate the cases where A and B are disconnected from C (allowing C to be 1), if C is disconnected from D or a new ‘other’ parent is added to D. If an other parent is added to D that causes D to be True, then both connections from E and G to F must be broken (hence the red lines). If D is still False, either the connection between E and F or G and F is also broken to make F have only one parent that is True. The final alternative is that the connection between F and H is broken or another parent is added to H. The results are convoluted in this case because the exclusion node is used as parent nodes rather than modifiers. Typically exclusion nodes should be used as modifiers and should not have children.

<img src="images/BayesFig19.png" width="450">

In the next case, F is an inversion node. In order for H to be true, F must be true, so connections between F and E, A, and G must be broken. Alternatively the connection between F and H can be broken or a new parent added to H.

<img src="images/BayesFig20.png" width="900">

In the next case, F is an inverted interaction node. In order for H to be true, F must be true, so connections between F and H must be broken. Note that connections between A, E, and G may be broken as well. The reason why there is no color is because all the associated probabilities and weights are 1, which means the gradient is near 0 (very flat) over a large range. If the magnitude of the initial randomization is increased above 0.5, these edges would become colored. Which paths are red or blue would be change every time the network is updated (see on the right).

<img src="images/BayesFig21.png" width="900">
