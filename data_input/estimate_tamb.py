"""
This file estimates Air Temperature for a site using latitude and longitude
on the basis of TMY data.

@author: DurejaBhavya
"""

import pandas as pd
from datetime import datetime
from datetime import timedelta, time


def estimate_air_temperature(df, latitude, longitude):
    """
    This function helps to estimate air temperature using latitude and
    longitude for any location using TMY (Typical Meteorological Year 2007-15).

    # read TMY from the European Commission's science and knowledge service
    #https://ec.europa.eu/jrc/en/PVGIS/tools/tmy#try-noninteractive

    Parameters
    ----------
    df: Pandas Dataframe
        dataframe containing weather information irradiance, module temperature
    latitude: float
        Longitude coordinate of the site
    longitude: float
        Longitude coordinate of the site

    Returns
    -------
    df: Pandas Dataframe
        dataframe with added module temperature column
    """
    # Defining the start year and end year using meteo data index
    df_year_start = df.index[0].year
    df_year_end = df.index[-1].year
    # fetching TMY data with API using latitude and longitude on hourly basis
    webUrl = 'https://re.jrc.ec.europa.eu/api/tmy?lat=' + \
             str(latitude) + '&lon=' + str(longitude) +\
             '&usehorizon=0&browser=1'
    # reading the data as csv
    try:
        output = pd.read_csv(webUrl, sep=',', header=0, skiprows=16,
                             skipfooter=12, engine='python')
    except ConnectionResetError:
        print("Unable to establish connection to the server for TMY data")
        sys.exit()

    # creating datetime column from UTC Time
    output.loc[:, 'datetime'] = [datetime.strptime(n, '%Y%m%d:%H%M') for n
                                 in output.loc[:, 'time(UTC)']]

    if df_year_start != df_year_end:
        # If data is needed for more than one year or if start year of data
        # is different than the end year of data
        first_index = output[(output.datetime.dt.month ==
                              df.index[0].month)
                             & (output.datetime.dt.day ==
                                df.index[0].day)].index
        # create two different parts of data for different years
        a = output.loc[:first_index[0] - 1, :]
        b = output.loc[first_index[0] - 1:, :]
        # Replace the year in these data parts accordingly
        b.loc[:, 'datetime'] = [n.replace(year=df_year_start) for n
                                in b.loc[:, 'datetime']]
        a.loc[:, 'datetime'] = [n.replace(year=meteo_year_end) for n in
                                a.loc[:, 'datetime']]
    else:
        # if both start year and end year is the same then we replace with
        # the same year for the whole data
        output.loc[:, 'datetime'] = [n.replace(year=df_year_start) for n
                                     in output.loc[:, 'datetime']]
    # setting the datetime as index
    output = output.set_index('datetime')
    output = output.sort_index(axis=0)
    # interpolating data at 1min basis
    output = output.resample('1min').fillna(method='ffill')
    # aligning the data with the meteo data
    output, _ = output.align(df, join='right', axis=0)
    # extracting only the temperature column from the output df
    est_air_temp = output['T2m']
    # adding a new index level to the df for tamb
    est_air_temp = (df * 0).add(est_air_temp, axis='rows').rename(
        columns={'G': 'Tamb'})
    df = pd.concat([df, est_air_temp], axis=1)

    return df
