"""
This notebook reads the system information.
@author: DurejaBhavya
"""

import pandas as pd

def gather_inputs(path_input_file):
    """
    This function reads the data input excel file and creates the general info
    and array info dataframes which contains site specific and input specific
    information.

    Parameters
    ----------
    path_input_file : str
        input sheet file path

    Returns
    -------
    array_info : multi-index Dataframe
        dataframe containing input specific information for all inputs.
    general_info : Dictionary
        a dictionary containing site specific information.
    """

    # READ INPUT EXCEL INFO SHEET
    # try:
    #     info_system = pd.read_excel(path_input_file,
    #                                 sheet_name='General Info')
    # except FileNotFoundError:
    #     sys.exit("Invalid input file.")

    info_system = pd.read_excel(path_input_file, sheet_name='General Info')

    # PRINT THE SYSTEM NAME
    strID = info_system.at[0, 'system_name']
    print('Selected system: ' + strID)

    # READ COMMON SYSTEM INFO
    IDi = 0

    # GENERAL INFORMATION ABOUT THE SITE
    general_info = dict()
    general_info['ID'] = strID
    general_info['name'] = info_system.at[IDi, 'system_name']
    general_info['address'] = info_system.at[IDi, 'address']
    general_info['city'] = info_system.at[IDi, 'city'].replace(" ", "")
    general_info['installed_capacity'] = info_system.at[IDi,
                                                        'system_total_installed_capacity']
    general_info['system_age'] = info_system.at[IDi, 'system_age']

    # GEOGRAPHICAL INFORMATION OF THE SITE
    general_info['lat'] = float(info_system.at[IDi, 'latitude'])
    general_info['long'] = float(info_system.at[IDi, 'longitude'])
    general_info['alt'] = float(info_system.at[IDi, 'altitude'])
    general_info['timezone'] = float(info_system.at[IDi, 'time_zone'])

    # DEFINING OTHER RELEVANT VARIABLES
    # ELECTRICITY PRICE
    general_info['electricity_price'] = float(info_system.at[IDi,
                                                             'electricity_price'])
    # CURRENCY USED
    general_info['monetary_unit'] = info_system.at[IDi, 'monetary_unit']
    # CO2 per kwh factor 1
    general_info['kg_CO2_per_kWh'] = info_system.at[IDi, 'kg_CO2_per_kWh']
    # site photo available to be put or report cover - Yes/No
    general_info['site_photo'] = info_system.at[IDi, 'site_photo']
    # Defines if meteo available - Yes/No
    general_info['meteo_info_available'] = info_system.at[IDi, 'meteo_info']
    # Defines the type of irradiance available - GHI/POA
    general_info['irradiance_type'] = info_system.at[IDi, 'irradiance_type']
    # Defines the date format of the inverter data
    general_info['date_format_inverter'] = info_system.at[IDi, 'date_format']
    # Defines the date format of the weather data
    general_info['date_format_meteo'] = info_system.at[IDi,
                                                       'date_format_meteo']
    # Time resolution of meteo data
    general_info['meteo_time_resolution'] = int(info_system.at[IDi,
                                                               'meteo_freq'])
    # Time resolution of inverter data
    general_info['inverter_time_resolution'] = int(info_system.at[IDi,
                                                                  'inv_freq'])

    # READ THE ARRAY INFO SHEET
    array_info_raw = pd.read_excel(path_input_file, sheet_name='Array Info')
    array_info = array_info_raw.iloc[:, 0:-11]
    # SETTING MULTI-INDEX
    idx = ['ag_level_2', 'ag_level_1']
    array_info = array_info.set_index(idx)
    array_info.loc[:, 'gamma'] = array_info.loc[:, 'gamma'] / 100  # GIVEN IN %
    array_info.loc[:, 'beta'] = array_info.loc[:, 'beta'] / 100  # GIVEN IN %
    array_info.loc[:, 'alpha'] = array_info.loc[:, 'alpha'] / 100  # GIVEN IN %
    # Converting kWatts into Watts
    array_info['installed_capacity'] = array_info['installed_capacity'] * 1000

    return array_info, general_info
