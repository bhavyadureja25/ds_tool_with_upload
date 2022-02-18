"""
This notebook reads the weather data.
@author: DurejaBhavya
"""

import pandas as pd
from os import sys
from data_input.add_multi_index_level import add_index_curve_level
from data_input.clean_using_pecos import pecos_clean
from data_input.estimate_tmod import estimate_module_temperature
from data_input.estimate_tamb import estimate_air_temperature


def read_weather_data(
        general_info,
        path_input_file):
    """
    This function reads the weather csv file and creates a multi-index
    dataframe containing GHI/G, Tmod and Tamb.

    Parameters
    ----------
    general_info: dataframe
        The dataframe with column which specifies irradiance is GHI or POA and
        dateformat of weather data
    path_input_file_meteo: str
        csv file path to read meteo data.
    path_input_file: Str
        input excel sheet path file containing column numbers of irradiance,
        Tamb and Tmod in meteo csv.

    Returns
    -------
    meteo_data = Multi index dataframe
        The dataframe containing G, Tamb and Tmod values.
    """
    # READ WEATHER DATA SHEET
    meteo_file = pd.read_excel(path_input_file, 
                                       sheet_name='Weather Data',skiprows=[0])
    print('meteo file read')
    # Reading array info
    array_info = pd.read_excel(path_input_file, sheet_name='Array Info')
    print('array_file_read')
    # Setting multi-level index for array info
    idx = ['ag_level_2', 'ag_level_1']
    array_info = array_info.set_index(idx)

    # Cleaning data with Pecos
    meteo_file = pecos_clean(meteo_file,
                             general_info['date_format_meteo'],
                             general_info['meteo_time_resolution'])
    print('cleaned_using_pecos')
    # Resetting the index
    meteo_file.index.rename('0', inplace=True)
    meteo_file.reset_index(inplace=True)

    # Converting column name to integers
    meteo_file.columns = [int(i) for i in meteo_file.columns]

    # Defining the final meteo frame variable to be returned by function
    meteo_data = pd.DataFrame()
    meteo_data_orig = pd.DataFrame()

    # CREATING DATETIME INDEX SERIES
    # Creating dataframe using column number given in array info
    meteo_datetime = meteo_file.loc[:, list(
        set(array_info.loc[:, 'datetime_column_meteo'].values))]
    # Converting column into datetime format
    meteo_datetime.iloc[:, 0] = pd.to_datetime(
        meteo_datetime.iloc[:, 0],
        format=general_info['date_format_meteo'])
    # Setting column name as datetime
    meteo_datetime.columns = ['datetime']

    # CREATING A IRRADIANCE DATAFRAME
    # Checking if irradiance data is provided by client or not
    if not all(pd.isnull(array_info.loc[:, 'irradiance_column'])):
        # If given, use column number given in array info to fetch data
        meteo_irradiance = meteo_file.loc[
                           :, array_info.loc[:, 'irradiance_column'].values]
        # Using array info to get same multi-index column name
        meteo_irradiance.columns = array_info.index
        # Setting datetime series as index
        meteo_irradiance = meteo_irradiance.set_index(
            meteo_datetime['datetime'])
        meteo_irradiance_orig = meteo_irradiance.copy()
    
        ## checking for % of data missing between 6am - 8 PM
        missing_irradiance = round(meteo_irradiance.between_time('06:00', '08:00').isna().sum().mean() / 
                                   meteo_irradiance.between_time('06:00', '08:00').sum().mean(),2)
        meteo_irradiance = meteo_irradiance.fillna(method = 'ffill').fillna(method='bfill')
        print('{} % of Irradiance Data is missing for analysis!'.format(
                missing_irradiance))
        
        # ADDING ANOTHER INDEX LEVEL WITH NAME FOR IRRADIANCE
        # Index name depends upon type of irradiance given general info-GHI/POA
        if general_info['irradiance_type'] == 'GHI':
            meteo_irradiance.columns = add_index_curve_level(
                meteo_irradiance.columns,
                'GHI')
            meteo_irradiance_orig.columns = add_index_curve_level(
                meteo_irradiance_orig.columns,
                'GHI')
        else:
            meteo_irradiance.columns = add_index_curve_level(
                meteo_irradiance.columns,
                'G')
            meteo_irradiance_orig.columns = add_index_curve_level(
                meteo_irradiance_orig.columns,
                'G')
        # Assigning meteo data as irradiance dataframe
        meteo_data = meteo_irradiance.copy()
        meteo_data_orig = meteo_irradiance_orig.copy()

    # CREATING A AMBIENT TEMPERATURE DATAFRAME
    # Checking if ambient temp is provided by client or not
    if not all(pd.isnull(array_info.loc[:, 'temperature_column'])):
        # If given, use column number given in array info to fetch data
        meteo_temperature = meteo_file.loc[
                            :, array_info.loc[:, 'temperature_column'].values]
        # Using array info to get same multi-index column name
        meteo_temperature.columns = array_info.index
        # Setting datetime series as index
        meteo_temperature = meteo_temperature.set_index(
            meteo_datetime['datetime'])

        ## checking for % of data missing between 6am - 8 PM
        missing_tamb = round(meteo_temperature.between_time('06:00', '08:00').isna().sum().mean() /
                                   meteo_temperature.between_time('06:00', '08:00').sum().mean(),2)
       
        meteo_temperature = meteo_temperature.fillna(method='ffill').fillna(method='bfill')
        print('{} % of Module Temp data is missing.'.format(missing_tamb))
    
        # ADDING ANOTHER INDEX LEVEL WITH NAME FOR Ambient Temp
        meteo_temperature.columns = add_index_curve_level(
            meteo_temperature.columns,
            'Tamb')
        # Adding ambient temp df to meteo df
        if meteo_data.empty:
            # if ambient temp not provided by client we estimate Tamb
            meteo_data = meteo_temperature.copy()
        else:
            # if ambinet temp is given by client we add it to the meteo df
            meteo_data = pd.concat([meteo_data, meteo_temperature], axis=1)
    else:
        # estimating module temperature
        meteo_data = estimate_air_temperature(meteo_data,
                                              latitude=general_info['lat'],
                                              longitude=general_info['long'])

    # CREATING A MODULE TEMPERATURE DATAFRAME
    # Checking if mod temp is provided by the client
    if not all(pd.isnull(array_info.loc[:, 'modtemperature_column'])):
        # If given, use column number given in array info to fetch data
        meteo_modtemp = meteo_file.loc[
                        :, array_info.loc[:, 'modtemperature_column'].values]
        # Using array info to get same multi-index column name
        meteo_modtemp.columns = array_info.index
        # Setting datetime series as index
        meteo_modtemp = meteo_modtemp.set_index(meteo_datetime['datetime'])

        ## checking for % of data missing between 6am - 8 PM
        missing_modtemp = round(meteo_modtemp.between_time('06:00', '08:00').isna().sum().mean() /
                                   meteo_modtemp.between_time('06:00', '08:00').sum().mean(),2)
        
        meteo_modtemp = meteo_modtemp.fillna(method = 'ffill').fillna(method='bfill')
        print('{} % of Module Temp data is missing.'.format(missing_modtemp))

        # CONVERTING MOD TEMP DATAFRAME INTO A MULTI-INDEX DATAFRAME
        meteo_modtemp.columns = add_index_curve_level(
            meteo_modtemp.columns,
            'Tmod')

        # Adding module temp df to meteo data df
        if meteo_data.empty:
            # if mod temp not provided by client we assign it as empty df
            meteo_data = meteo_modtemp.copy()
        else:
            meteo_data = pd.concat([meteo_data, meteo_modtemp], axis=1)
    else:
        # estimating module temperature using irradiance and ambient temp
        meteo_data = estimate_module_temperature(meteo_data, irr_str='G',
                                                    tamb_str='Tamb')

    # Swapping index level to get the recently added level at the bottom
    meteo_data = meteo_data.swaplevel(0, 1, axis=1).swaplevel(1, 2, axis=1)
    meteo_data = meteo_data.sort_index(axis=1, level=[0, 1])

    meteo_data_orig = meteo_data_orig.swaplevel(0, 1, axis=1).swaplevel(1, 2, axis=1)
    meteo_data_orig = meteo_data_orig.sort_index(axis=1, level=[0, 1])

    return meteo_data,meteo_data_orig


def irradiance_data(general_info, path_input_file_meteo,
        path_input_file):
    """
    This function outputs only the unique irradiance columns data.
    Parameters
    ----------
    general_info: dataframe
        The dataframe with column which specifies irradiance is GHI or POA and
        dateformat of weather data
    path_input_file_meteo: str
        csv file path to read meteo data.
    path_input_file: Str
        input excel sheet path file containing column numbers of irradiance,
        Tamb and Tmod in meteo csv.

    Returns
    -------
    irradiance_df : Pandas Dataframe
        Data frame caintaining the irradiance columns
    """
    # reading the meteo data csv
    try:
        meteo_file = pd.read_csv(path_input_file_meteo, skiprows=[0])
    except FileNotFoundError:
        sys.exit("Invalid weather data file.")

    # Reading array info
    array_info = pd.read_excel(path_input_file, sheet_name='Array Info')
    # Setting multi-level index for array info
    idx = ['ag_level_2', 'ag_level_1']
    array_info = array_info.set_index(idx)

    # Cleaning data with Pecos
    meteo_file = pecos_clean(meteo_file,
                             general_info['date_format_meteo'],
                             general_info['meteo_time_resolution'])
    # Resetting the index
    meteo_file.index.rename('0', inplace=True)
    meteo_file.reset_index(inplace=True)

    # Converting column name to integers
    meteo_file.columns = [int(i) for i in meteo_file.columns]

    # CREATING DATETIME INDEX SERIES
    # Creating dataframe using column number given in array info
    meteo_datetime = meteo_file.loc[:, list(
        set(array_info.loc[:, 'datetime_column_meteo'].values))]
    # Converting column into datetime format
    meteo_datetime.iloc[:, 0] = pd.to_datetime(
        meteo_datetime.iloc[:, 0],
        format=general_info['date_format_meteo'])
    # Setting column name as datetime
    meteo_datetime.columns = ['datetime']

    # CREATING A IRRADIANCE DATAFRAME
    # Creating a new dataframe irradiance_plot of unique irradiance data only
    if not all(pd.isnull(array_info.loc[:, 'irradiance_column'])):
        # If given, use column number given in array info to fetch data of
        # uniuqe irradiance columns
        irradiance_cols = list(set(array_info.loc[:, 'irradiance_column']))
        irradiance_df = pd.DataFrame(meteo_file.loc[:, irradiance_cols])
        col_name = ['Irr'+str(i+1) for i in range(0,
                                                  len(irradiance_df.columns))]
        irradiance_df.columns = col_name
        # setting datetime as index
        irradiance_df = irradiance_df.set_index(
            meteo_datetime['datetime'])

    return irradiance_df
