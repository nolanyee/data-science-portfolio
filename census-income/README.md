# Income Class Prediction from Census Data
*Skills: R, Visualization, Imputation, Machine Learning*

This project involves predicting income class (binary classification) from census data. Due to the large size of the data set, the processing is split into 3 notebooks and intermediate results are saved and re-imported in order to release memory from previous steps. In addition, since the classes are heavily imbalanced, subsampling is used on the larger class in order to create different models that are ensembled at the end. The features are unique in that features are undefined ("not in universe") for some levels of other features. For this reason, a simple linear model is not used. Though interactions could account for this complexity, it was easier to use a decision tree model instead.

For more details, see the PDF file of the Jupyter Notebook. A PDF is included for faster loading and a more pleasant read since it displays without expanding all the output windows. For code and data reviewing purposes, the original Jupyter Notebook file is also included in this repository along with the datasets.
