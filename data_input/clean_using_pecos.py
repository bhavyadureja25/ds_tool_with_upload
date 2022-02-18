"""
This notebook reads the weather data.
@author: DurejaBhavya
"""


import pecos
import pandas as pd


def pecos_clean(df_in, date_format, time_frequency):
    """
    This function helps to clean a time series dataframe by removing duplicate
    indices or creating missing timestamps (with nan in each columns) to get a
    continuous dataframe. Note : the first column should be datetime.

    Parameters
    ----------
    df_in : dataframe
        the dataframe to be checked for missing/ duplicate timestamps
    date_format : string for example "Y%-m%-d%"
        date format of the first column of the dataframe
    time_frequency : float (in minutes)
        The time resolution of the dataframe

    Returns
    -------
    df_cleaned : dataframe
        the dataframe with index with no missing/duplicate timestamp.
    """

    df = df_in.copy()
    df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0], format=date_format)
    df = df.set_index(df.iloc[:, 0])
    df = df.iloc[:, 1:]
    df.index = df.index.round(str(time_frequency) + 'min')

    # initializing pecos
    pecos.logger.initialize()
    pm = pecos.monitoring.PerformanceMonitoring()
    # adding dataframe to be cleaned
    pm.add_dataframe(df)
    # Time frequency needs to be specified in seconds
    pm.check_timestamp(time_frequency*60)
    # # Prints the errors found with timestamps
    # print(pm.test_results)
    # pecos.io.write_test_results(pm.test_results)
    # pecos.io.write_monitoring_report(pm.data, pm.test_results)
    # Saving the clean dataframe
    df_cleaned = pm.cleaned_data
    print('Cleaned Data using Pecos')

    return df_cleaned
