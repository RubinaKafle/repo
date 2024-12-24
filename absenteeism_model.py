#!/usr/bin/env python
# coding: utf-8

# In[11]:


import numpy as np
import pandas as pd
import pickle
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import StandardScaler

class CustomScaler(BaseEstimator,TransformerMixin): 
    
    def __init__(self,columns,copy=True,with_mean=True,with_std=True):
        
        self.columns = columns
        self.copy = copy
        self.with_mean = with_mean
        self.with_std = with_std
        
        self.scaler = StandardScaler(copy,with_mean,with_std)
        
        self.mean_ = None
        self.var_ = None

    def fit(self, X, y=None):
        self.scaler.fit(X[self.columns], y)
        self.mean_ = np.array(np.mean(X[self.columns]))
        self.var_ = np.array(np.var(X[self.columns]))
        return self

    def transform(self, X, y=None, copy=None):
        init_col_order = X.columns
        X_scaled = pd.DataFrame(self.scaler.transform(X[self.columns]), columns=self.columns)
        X_not_scaled = X.loc[:,~X.columns.isin(self.columns)]
        return pd.concat([X_not_scaled, X_scaled], axis=1)[init_col_order]

class absenteeism_model():
    def __init__(self, model_file, scaler_file):
        # read model and scaler files
        with open('model','rb') as model_file , open('scaler','rb') as scaler_file:
            self.reg = pickle.load(model_file)
            self.scaler = pickle.load(scaler_file)
            self.data = None

    # take data file (*.csv) and preprocess it 
    def load_and_clean(self, data_file):
        df = pd.read_csv(data_file, delimiter=',')
        # store the data in a new variable(copy it)
        self.df_with_predictions = df.copy()
        # drop ID column
        df = df.drop(['ID'], axis=1)
        # to preserve the code we've created in the previous section, we will add a column with 'NaN' strings
        df['Absenteeism Time in Hours'] = 'NaN'

        # create a separate dataframe, containing dummy values for ALL avaiable reasons
        reason_columns = pd.get_dummies(df['Reason for Absence'], drop_first = True)

        # split reason_columns into 4 types
        reason_type_1 = reason_columns.loc[:, :14].max(axis=1)
        reason_type_2 = reason_columns.loc[:, 15:17].max(axis=1)
        reason_type_3 = reason_columns.loc[:, 18:21].max(axis=1)
        reason_type_4 = reason_columns.loc[:, 22:].max(axis=1)

        # to avoid multicollinearity, drop the 'Reason for Absence' column from df
        df = df.drop(['Reason for Absence'], axis = 1)  

         # concatenate df and the 4 types of reason for absence
        df = pd.concat([df, reason_type_1, reason_type_2, reason_type_3, reason_type_4], axis = 1)

        # assign names to the 4 reason type columns
        # note: there is a more universal version of this code, however the following will best suit our current purposes             
        column_names = ['Date', 'Transportation Expense', 'Distance to Work', 'Age',
                           'Daily Work Load Average', 'Body Mass Index', 'Education', 'Children',
                           'Pets', 'Absenteeism Time in Hours', 'reason_type_1', 'reason_type_2', 'reason_type_3', 'reason_type_4']
        df.columns = column_names

        # reorder the columns in df
        column_names_reordered =  ['reason_type_1', 'reason_type_2', 'reason_type_3', 'reason_type_4', 'Date', 'Transportation Expense', 
                                      'Distance to Work', 'Age', 'Daily Work Load Average', 'Body Mass Index', 'Education', 
                                      'Children', 'Pets', 'Absenteeism Time in Hours']
        df = df[column_names_reordered]

        # convert date to date time
        df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')

        # cretae a list of months from date colum and add a new colum for month
        df['Month Value'] = [x.month for x in df['Date']]

        # create a new feature called day of week
        df['Day of the Week'] = df['Date'].apply(lambda x:x.weekday())

        # drop thedate column
        df = df.drop(['Date'],axis=1)

        # re-order the columns in df
        column_names_upd = ['reason_type_1', 'reason_type_2', 'reason_type_3', 'reason_type_4', 'Month Value', 'Day of the Week',
                                'Transportation Expense', 'Distance to Work', 'Age',
                                'Daily Work Load Average', 'Body Mass Index', 'Education', 'Children',
                                'Pets', 'Absenteeism Time in Hours']
        df = df[column_names_upd]
        
        # map 'Education' variables; the result is a dummy
        df['Education'] = df['Education'].map({1:0, 2:1, 3:1, 4:1})

        # replace the NaN values
        df = df.fillna(value=0)

        # drop the original absenteeism time
        df = df.drop(['Absenteeism Time in Hours'],axis=1)

        # drop the variables we decide we don't need
        df = df.drop(['Day of the Week','Daily Work Load Average','Distance to Work'],axis=1)
            
        # we have included this line of code if you want to call the 'preprocessed data'
        self.preprocessed_data = df.copy()

        # we need this line so we can use it in the next functions
        self.data = self.scaler.transform(df)


    def predicted_probability(self):
        if (self.data is not None):  
            pred = self.reg.predict_proba(self.data)[:,1]
            return pred
        
    # a function which outputs 0 or 1 based on our model
    def predicted_output_category(self):
        if (self.data is not None):
            pred_outputs = self.reg.predict(self.data)
            return pred_outputs
        
    # predict the outputs and the probabilities and 
    # add columns with these values at the end of the new data
    def predicted_outputs(self):
        if (self.data is not None):
            self.preprocessed_data['Probability'] = self.reg.predict_proba(self.data)[:,1]
            self.preprocessed_data ['Prediction'] = self.reg.predict(self.data)
            return self.preprocessed_data


# In[ ]:




