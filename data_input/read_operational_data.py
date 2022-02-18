# -*- coding: utf-8 -*-
"""
This notebook reads the operational data (current & voltage).
@author: DurejaBhavya
"""

import pandas as pd
from os import sys
from data_input.add_multi_index_level import add_index_curve_level
from data_input.clean_using_pecos import pecos_clean

def read_inverter_data(general_info, path_input_file):
    
    # reads data 
    data_file = pd.read_excel(path_input_file, 
                               sheet_name='Inverter Data',skiprows=[0])
    data_points = data_file.iloc[:,1:].size
    # Cleaning data using Pecos
    data_file = pecos_clean(data_file,
                            general_info['date_format_inverter'],
                            general_info['inverter_time_resolution'])
    print('percos cleaning complete')
    # Resetting the index
    data_file.index.rename('0', inplace=True)
    data_file.reset_index(inplace=True)
    # Converting column names to integers
    data_file.columns = [int(i) for i in data_file.columns]

    # Reading array info
    array_info = pd.read_excel(path_input_file, sheet_name='Array Info')
    print('array_info_read')

    # SETTING MULTI-INDEX IN ARRAY INFO
    idx = ['ag_level_2', 'ag_level_1']
    array_info = array_info.set_index(idx)

    # Creating Datetime series to be used as index
    inputs_datetime = data_file.loc[:, list(
        set(array_info.loc[:, 'datetime_column'].values))]

    inputs_datetime.iloc[:, 0] = pd.to_datetime(
        inputs_datetime.iloc[:, 0],
        format=general_info['date_format_inverter'])

    # setting index name as datetime
    inputs_datetime.columns = ['datetime']

    #  CREATING CURRENT DATAFRAME USING ARRAY INFO CURRENT COLUMN NUMBERS
    inputs_current = data_file.loc[:, array_info.loc[:, 'current_column'].values]
    inputs_current.columns = array_info.index
    inputs_current = inputs_current.set_index(inputs_datetime['datetime'])

    #  CREATING VOLTAGE DATAFRAME USING ARRAY INFO VOLTAGE COLUMN NUMBERS
    inputs_voltage = data_file.loc[:, array_info.loc[:, 'voltage_column'].values]
    inputs_voltage.columns = array_info.index
    inputs_voltage = inputs_voltage.set_index(inputs_datetime['datetime'])

    # CALCULATING POWER VALUES AS I*V IF NOT PROVIDED IN INVERTER DATA
    if all(pd.isnull(array_info.loc[:, 'power_column'])):
        inputs_power = inputs_current * inputs_voltage
    else:
        inputs_power = data_file.loc[:, array_info.loc[:, 'power_column'].values]
        inputs_power.columns = array_info.index
        inputs_power = inputs_power.set_index(inputs_datetime['datetime'])

    # CONVERTING I, P, V DATAFRAME INTO MULTI-INDEX DATAFRAMES
    inputs_current.columns = add_index_curve_level(inputs_current.columns, 'I')
    inputs_voltage.columns = add_index_curve_level(inputs_voltage.columns, 'V')
    inputs_power.columns = add_index_curve_level(inputs_power.columns, 'P')

    # CONCATENATING I,P,V INTO A SINGLE MULTI-INDEX DATAFRAME
    inverter_data = pd.concat([inputs_current,
                               inputs_voltage,
                               inputs_power],
                              axis=1)
    # Swapping index level to get recently added index level at the bottom
    inverter_data = inverter_data.swaplevel(
        0, 1, axis=1).swaplevel(1, 2, axis=1)
    inverter_data = inverter_data.sort_index(axis=1, level=[0, 1])
    print('inverter_data_now_complete')

    return inverter_data, data_points
