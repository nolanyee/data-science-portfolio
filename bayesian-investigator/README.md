# Bayesian Network Investigator
*Skills: Python, Probability, Algorithms, Gradient Descent*

### Overview
This prototype application is intended to facilitate construction of Bayesian networks and serve as a simpler version of a Bayesian network in cases where the joint probabilities for each node are mostly unknown and there is not enough data to learn them. It is also able to show paths and nodes in the network that are suspect when contradictory evidence is given.

### Theoretical Background
__Notation__\
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
and the conditional probability of a node being true (given the state of the parents P_i) is a function of the weights\
p(T|P_1⋯P_n )=f(w_1,⋯,w_n )
