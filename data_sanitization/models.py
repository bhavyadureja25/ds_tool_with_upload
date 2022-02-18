"This file contains model machine learning models for predicting missing data"

from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
import pandas as pd
import numpy as np
import time

def resampling_meteo(m_data, general_info):
    if general_info['meteo_time_resolution'] != \
            general_info[ 'inverter_time_resolution']:
        freq = general_info[ 'inverter_time_resolution']
        m_data_resampled = m_data.resample(str(freq)+'min').mean()
        return m_data_resampled

def predict_missing_data(inv_data, meteo_data, array_info, general_info):

    # timer starts here
    start_time = time.time()

    # creating opy of the dataframes
    inv_df = inv_data.copy()
    meteo_df = meteo_data.copy()

    # defining the Output dataframe variable
    result_df = pd.DataFrame(index = inv_df.index)

    # resampling meteo data if time freq is not same
    meteo_df = resampling_meteo(m_data=meteo_df, general_info=general_info)

    # Concatenating inverter and meteo to get a single dataframe
    final_df = pd.concat([inv_df, meteo_df], axis=1)

    # joining column level to get list of all column name
    final_df.columns = final_df.columns.map('-'.join)

    # using input name index as its index is a list of input names
    for inv_name in array_info['input_name']:
        # extracting all column names which starts with selected inverter name
        filter_col = [col for col in final_df if col.startswith(inv_name)]
        filter_col = filter_col
        # filtering these column from dataframe
        df_f = final_df[filter_col]

        # creating new feature of unix timestamp
        df_f[inv_name + '-' +'unix'] = df_f.index.astype(np.int64) // 10 ** 9

        # predicting Voltage using module temp, irradiance and unix time
        v_column = inv_name + '-' + 'V'
        i_column = inv_name + '-' + 'I'
        if df_f[v_column].isnull().sum() > 0:
            predictors = [inv_name + '-' + var for var in
                          ['G', 'Tmod', 'unix']]
            # train and test split
            xtest = df_f[predictors][np.isnan(df_f[v_column])]
            ytest = df_f[[v_column]][np.isnan(df_f[v_column])]
            xtrain = df_f[predictors][~df_f.index.isin(xtest.index)]
            ytrain = df_f[[v_column]][~df_f.index.isin(ytest.index)]

            # scaling the data
            xtrain_s, xtest_s = scaler(xtrain, xtest)

            # Ridge regression
            yhat_train, yhat_test = ridge_regression(xtrain_s, xtest_s,
                                                     ytrain, alpha=1)
            ytest[v_column] = yhat_test
            y_var = pd.concat([ytrain, ytest])
            df_f[v_column] = y_var

        # predicting Current using V, G, unix time and Module temp
        if df_f[i_column].isnull().sum() > 0:
            predictors = [inv_name + '-' + var for var in
                          ['V', 'G','Tmod', 'unix']]
            # train and test split
            xtest = df_f[predictors][np.isnan(df_f[i_column])]
            ytest = df_f[[i_column]][np.isnan(df_f[i_column])]
            xtrain = df_f[predictors][~df_f.index.isin(xtest.index)]
            ytrain = df_f[[i_column]][~df_f.index.isin(ytest.index)]

            # scaling the data
            xtrain_s, xtest_s = scaler(xtrain, xtest)

            # Ridge regression
            yhat_train, yhat_test = ridge_regression(xtrain_s, xtest_s,
                                                     ytrain, alpha=1)
            ytest[i_column] = yhat_test
            y_var = pd.concat([ytrain, ytest])
            df_f[i_column] = y_var

        # assigning the final and filled columns to output dataframe
        result_df[v_column] = df_f[v_column]
        result_df[i_column] = df_f[i_column]

    # timer ends here
    end_time = time.time()
    print('\nModel Execution Time:{} seconds'.format(end_time-start_time))
    return result_df

def scaler(xtrain, xtest):
    scaler = StandardScaler()
    xtrain_s = scaler.fit_transform(xtrain)
    xtest_s = scaler.transform(xtest)
    return xtrain_s, xtest_s

def ridge_regression(xtrain, xtest, ytrain,alpha=1):
    # define model
    model = Ridge(alpha=alpha)
    model.fit(xtrain, ytrain)
    yhat_train = model.predict(xtrain)
    yhat_test = model.predict(xtest)
    return yhat_train, yhat_test

