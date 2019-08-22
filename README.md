# Data Science Portfolio

This repository is a portfolio of all my self-study projects and other coding side projects. It contains Jupyter Notebooks using Python or R, as well as scripts/applications written in Python. The repository has a subfolder for each project, containing the code in .ipynb files or .py files, as well as relevant data sets. For quick perusal, the links below point to README files or PDF versions of the Jupyter Notebook. 

The projects focus on solving interesting and diverse problems using a variety of different techniques.

### Highlights
[Depth Map Generator](depth-map-generator/README.md)\
[Music Transcriber](music-transcriber/README.md)\
[Literary Pattern Analyzer](literary-pattern-analyzer/README.md)\
[Bayesian Network Investigator](bayesian-investigator/README.md)\
[Movie Recommender Model](movie-recommender/MovieRecommenderSystem.pdf)\
[Maze and Labyrinth Generator](maze-labyrinth-generator/README.md)

#### *Skills Summary*
*Python, R, image processing, audio processing, natural language processing, statistics, linear algebra, multivariable calculus, visualization, feature extraction, imputation, machine learning, forecasting, simulation, neural networks, and algorithms*

*Python Libraries: pandas, numpy, scipy, sklearn, statsmodels, matplotlib, tensorflow, symengine, tkinter, nltk, beautifulsoup*

*R Libraries: dplyr, caret, forecast*

# Contents

## Unstructured Data Analysis and Processing

* __Image Processing__
  * [__Depth Map Generator__](depth-map-generator/README.md): Generates normal maps and depth maps from monocular images of  monochromatic matte bas-reliefs. The application is primarily for use in texturing 3D models. This program uses physical and mathematical approaches to solve this challenging problem.
    * *Skills: Python, Image Processing, Linear Algebra, Multivariable Calculus, Visualization*
  
  * [__Style Transfer Implementation__](style-transfer/README.md): Inputs an image of a painting and a photograph, and applies the painting style to the photograph using a pre-trained convolutional neural network. This is a flexible implementation of L. A. Gatys, A. S. Ecker, M. Bethge. Image Style Transfer Using Convolutional Neural Networks. In IEEE Conference on Computer Vision and Pattern Recognition (CVPR), 2016.
  
    * *Skills: Python, Image Processing, Convolutional Neural Networks, Gradient Descent*
  
  * [__Handwritten Digit Recognition__](digit-recognition/HandwrittenDigitRecognition.pdf): Uses a neural network to classify handwritten digits from the NIST dataset - a classic problem, but a useful introduction to image recognition.
    * *Skills: Python, Image Recognition, Neural Networks*

* __Audio Processing__
  * [__Music Transcriber__](music-transcriber/README.md): A rudimentary polyphonic music transcription algorithm, primarily focused on classical music. This program uses Fourier Transform, Harmonic Sum Spectra, second derivative peak detection, and linear modeling, among other techniques, to generate the final score.
    * *Skills: Python, Audio Processing, Calculus*

* __Natural Language Processing__
  * [__Literary Pattern Analyzer__](literary-pattern-analyzer/README.md): Visualization tools for finding structural literary patterns in ancient texts. The plots include a custom lexical dispersion plot with variable bar length based on word frequency within verses, a word intentionality plot based on the binomial distribution, a parallelsim arc plot based on Jaccard similarity and order similarity, and a topic plot generated using Latent Dirichlet Allocation.
    * *Skills: Python, Natural Language Processing, Visualization*
  
  * [__Twitter Hate Speech Detection__](hate-speech-detection/Twitter%20Hate%20Speech%20Detection.pdf): Identifies tweets containing hate speech. This analysis uses a depth first search algorithm for splitting hashtags, and tf-idf for feature generation.
    * *Skills: Python, Natural Language Processing, Feature Extraction, Algorithms, Machine Learning*
  
  * [__Recipe Nationality Classification__](recipe-nationality/RecipeNationalityClassification.pdf): Classification of recipies by country of origin based on the lists of ingredients. This analysis uses tf-idf for generation of the sparse feature matrix.
    * *Skills: Python, Natural Language Processing, Machine Learning*
  
## Structured Data Analysis

* __R Projects__
  * [__Human Activity Recognition__](human-activity-recognition/HumanActivityRecognition.pdf): Classification of samples into one of six possible activities based on features extracted from motion sensors. The data set contains 561 features derived from time series data from a waist sensor.
    * *Skills: R, Machine Learning*
  
  * [__Transportation Usage Forecasting__](transportation-usage/TransportationUsageForecasting.pdf): Forecasting the number of passengers on a new transit system based on historical data. The series is decomposed as a multiplicative time series. The components are trend, seasonality, and remainder. The remainder component is stationary and thus is modeled with ARIMA. The trend is modeled using nonlinear regression.
    * *Skills: R, Visualization, Time Series Analysis, Nonlinear Regression*
  
  * [__Grocery Sales Prediction__](grocery-sales/GrocerySalesPrediction.pdf): Prediction of sales of grocery items in different grocery stores. This analysis involves feature extraction, and evaluates a linear model and decision tree model to solve the regression problem.
    * *Skills: R, Feature Extraction, Visualization, Machine Learning*
  
  * [__Census Income Prediction__](census-income/CensusIncomePrediction.pdf): Prediction of income class from census data. Due to the large size of the data set, the processing is split into 3 notebooks and intermediate results are saved and re-imported in order to release memory from previous steps. In addition, since the classes are heavily imbalanced, subsampling is used on the larger class in order to create different models that are ensembled at the end.
    * *Skills: R, Visualization, Imputation, Machine Learning*
  
  * [__Loan Status Prediction__](loan-status/LoanStatusPrediction.pdf): Prediction of loan approval status based on demographic and applicant history data. This is a classification problem.
    * *Skills: R, Visualization, Machine Learning*
 
* __Python Projects__

  * [__Movie Recommender Model__](movie-recommender/MovieRecommenderSystem.pdf): Custom recommender model, developed and optimized using a 1 million movie rating dataset from MovieLens. The model is a weighted combination of collaborative filtering and content-based models. A combination of demographic data, movie genre, and latent factors extracted using non-negative matrix factorization are used to calculate custom similarity functions.
    * *Skills: Python, Linear Algebra, Feature Extraction, Optimization, Visualization*
  
  * [__Black Friday Sales Prediction__](black-friday-sales/BlackFridaySales.pdf): Analysis of consumer demographic data, past spending, and product category data, using regression models to predict the amount that given consumers will spend on certain products on Black Friday.
    * *Skills: Python, Data Cleaning, Feature Extraction, Visualization, Machine Learning, Feature Selection*
  
  * [__Titanic Survival Prediction__](titanic-survival/TitanicSurvivalPrediction.pdf): The classic problem involving prediction of passenger survival on the Titanic, but with an emphasis on feature extraction from text, including prediction of ethnicity and imputation techniques.
    * *Skills: Python, Feature Extraction, Imputation, Visualization, Machine Learning, Feature Selection*
  
  * [__Iris Species Classification__](iris-classification/IrisClassification.pdf): Evaluation of common machine learning algorithms for the classic Iris dataset.
    * *Skills: Python, Visualization, Machine Learning*

## Probability

  * [__Bayesian Network Investigator__](bayesian-investigator/README.md): A prototype application intended to facilitate construction of Bayesian networks and serve as a simpler version of a Bayesian network in cases where the joint probabilities for each node are mostly unknown and there is not enough data to learn them. It is also able to show paths and nodes in the network that are suspect when contradictory evidence is given.
     * *Skills: Python, Probability, Algorithms, Gradient Descent*
  
  * [__Poker AI__](poker-ai/README.md): A simple straight heads-up poker game simulation. The player and computer are each dealt a 5 card hand, with no drawing. The algorithm uses card counting, combinatorics, probability, logistic regression, and heuristics.
    * *Skills: Python, Probability*
  

## Computer Science
  * [__Maze and Labyrinth Generator__](maze-labyrinth-generator/README.md): A program that generates and solves random mazes *and* labyrinths of variable size (a labyrinth contains only one path and no branches). It also allows the user to move a turtle around the maze and has a toggle button to show and hide the solution.
    * *Skills: Python, Algorithms, Data Structures*
  
  * [__Unbeatable Tic-Tac-Toe AI__](unbeatable-tic-tac-toe-ai/README.md): A Tic-Tac-Toe AI that has 3 levels of difficulty. The Hard mode is unbeatable. Rather than using the common minimax algorithm, this AI uses a unique deterministic algorithm based on linear algebra to solve this classic problem.
    * *Skills: Python, Linear Algebra*
  
  * [__Sudoku Solver__](sudoku-solver/README.md): A program that solves any solvable Sudoku puzzle and can generate random solvable puzzles. The algorithm is based on set theory and depth first search.
    * *Skills: Python, Algorithms*
  
  * [__Final Exam Scheduler__](final-exam-scheduler/README.md): A program uses graph coloring theory to generate a final exam schedule from students' enrollment data. It includes a Monte-Carlo simulation function to profile time complexity.
    * *Skills: Python, Algorithms, Monte-Carlo Simulation*
  
  * [__Flock Simulator__](flock-simulator/README.md): A program that simulates a flock of birds in flight (or perhaps a swarm of bees). The birds are trapped in the window and fly around. The user can act as a predator and chase the birds around the window.
    * *Skills: Python, Linear Algebra*
