# -*- coding: utf-8 -*-
"""WeightedRandomForest.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1x7ycRiU5XnYtWn4esCbPlu0ijpx4lOR8
"""

#import modules
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sklearn.model_selection as ms
from sklearn.model_selection import train_test_split
from sklearn import tree
from sklearn import ensemble
import re
from sklearn.metrics import confusion_matrix

#Import dataset

# trimmed2018 = pd.read_csv('cdc2018trimmed.csv') #(84)

# csv2018 = pd.read_csv('CSV2018.csv') # with bettina's function as well, (98 lol)

trimwolabor2018 = pd.read_csv('cdc2018wolabor.csv') #(68)

# trimmed2 = pd.read_csv('cdc2018trimmed2.csv') #(84)

# trimmed2016 = pd.read_csv("CDC2016trimmed.csv") #84.9

# trimwolabor2016 = pd.read_csv('CDC2016wolabor.csv') #67.3

# trimmed2017 = pd.read_csv('CDC2017trimmed.csv') #84.8

#remove unknown AB_NICUs
trimwolabor2018 = trimwolabor2018[trimwolabor2018['AB_NICU'].isin(['Y', 'N'])]

def add_random_column_to_df (dataframe):
    import random
    mylist = []
    for i in range(0, dataframe.shape[0]):
        x = random.randint(1,1000)
        mylist.append(x)
    dataframe['RANDOM'] = mylist

    return dataframe

trimwolabor2018 = add_random_column_to_df(trimwolabor2018)

# function to split out holdout test set
def split_sets(dataframe, seed, test_prop=0.1): 
    '''
    - A function that splits specifically a dataframe into a train and test portion
    - Requires multiple assignment: train, test
    ---------------
    - dataframe: dataframe to be split
    - seed: set seed for reproducability
    - test_prop: takes a float - proportion of dataframe that should be allocated to the test set
    '''

    np.random.seed(seed)
    testIdxes = np.random.choice(range(0,dataframe.shape[0]), size=round(dataframe.shape[0]*test_prop), replace=False)
    trainIdxes = list(set(range(0,dataframe.shape[0])) - set(testIdxes))

    train = dataframe.iloc[trainIdxes,:]
    test  = dataframe.iloc[testIdxes,:]
    
    return train, test

train, test = split_sets(trimwolabor2018, 0, test_prop=0.1)

print(train.shape)
print(test.shape)

dsample = train.copy()

#LabelEncoding Function. Thanks Ira!
def LabelEncoding(dataframe):
    '''
    Function that takes a dataframe and transforms it with label encoding on all the categorical features.
    '''
    
    import pandas as pd
    
    #create a list using object types since dataframe.dtypes.value_counts() only shows objects and int64
    objlist = list(dataframe.select_dtypes(include=['object']).columns)
    
    #change type then transform column using cat codes
    for col in objlist:
        dataframe[col] = dataframe[col].astype('category')
        dataframe[col] = dataframe[col].cat.codes
    
    return dataframe

#Label Encoded
dsample = LabelEncoding(dsample)
dtest = LabelEncoding(test)

#test train split
X_train = dsample.drop('AB_NICU', axis=1)
y_train = dsample['AB_NICU']
X_test = dtest.drop('AB_NICU', axis=1)
y_test = dtest['AB_NICU']

#RANDOM FOREST INITIAL FIT-
randomForest = ensemble.RandomForestClassifier(class_weight='balanced')
randomForest.set_params(random_state=0)
randomForest.fit(X_train, y_train) 
print("The training error is: %.5f" % (1 - randomForest.score(X_train, y_train)))
print("The test     error is: %.5f" % (1 - randomForest.score(X_test, y_test)))

# Commented out IPython magic to ensure Python compatibility.
# set the parameter grid
grid_para_forest = {
    'criterion': ['gini', 'entropy'],
    'max_depth': range(1, 16),
    'n_estimators': range(10, 50, 30)
}
# GRID SEARCH
grid_search_forest = ms.GridSearchCV(randomForest, grid_para_forest, scoring='precision', cv=5, n_jobs=-1,)
# %time grid_search_forest.fit(X_train, y_train)

#Best Params and Score
print(grid_search_forest.best_params_)
grid_search_forest.best_score_

# get the training/test errors
print("The training error is: %.5f" % (1 - grid_search_forest.best_estimator_.score(X_train, y_train)))
print("The test     error is: %.5f" % (1 - grid_search_forest.best_estimator_.score(X_test, y_test)))

#list of feature importance
feature_importance = list(zip(dsample.columns, randomForest.feature_importances_))
dtype = [('feature', 'S10'), ('importance', 'float')]
feature_importance = np.array(feature_importance, dtype=dtype)
feature_sort = np.sort(feature_importance, order='importance')[::-1]
[i for (i, j) in feature_sort[0:10]]

#CONFUSION MATRIX
cm = confusion_matrix(y_test, grid_search_forest.best_estimator_.predict(X_test))
cm

#Sorting feature importance
sorted_features = sorted(feature_importance, key=lambda x: x[1], reverse=True)
sorted_features

# Plot
features_top10 = sorted_features[:10]
featureNames, featureScores = zip(*list(features_top10))
plt.barh(range(len(featureScores)), featureScores, tick_label=featureNames)
plt.title('feature importance')

#Thanks Drucila!
feature_importance = 100.0 * (randomForest.feature_importances_ / randomForest.feature_importances_.max())
important_features = X_train.columns[feature_importance >= 10]
unimportant_features = X_train.columns[feature_importance < 5]

important_features

unimportant_features