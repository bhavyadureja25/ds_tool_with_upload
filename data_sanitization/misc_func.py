import pandas as pd
import numpy as np


def data_summary_table(total_data, missing_data,outlier_data, resolution):
    """
    # total number of data points
    # temporal resolution
    # % of outliers data points
    # % missing data points

    :param total_data: total number of datapoints received in raw data
    :param missing_data: % of data missing
    :param outlier_data: % of outliers found
    :param resolution: time freq of inverter data

    :return: data summary table consisting info on these 4 columns
    """

    data_summary = pd.DataFrame(index=['Data Points Available',
                                         'Temporal Resolution', 'Missing Data (%)',
                                         'Outliers (%)'], columns=['Values'])

    data_summary.loc['Data Points Available'] = str(total_data/1000) + ' K'
    data_summary.loc['Temporal Resolution'] = str(resolution) + ' Mins'
    data_summary.loc['Missing Data (%)'] = str(missing_data) + ' %'
    data_summary.loc['Outliers (%)'] = str(outlier_data) + ' %'

    return data_summary

