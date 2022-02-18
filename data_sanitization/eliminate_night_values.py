# -*- coding: utf-8 -*-
"""
Created on Tue Dec 21 08:05:37 2021

@author: Krithika
"""

import pandas as pd
import numpy as np


def eliminate_nightvalues(data, cs_data, threshold=0):
    '''
    This function is used to filter out the night time values by using the
    POA irradiance obtained using clearsky GHI.

    Parameters
    ----------
    meteo_data : pandas.Dataframe
        MultiIndex dataframe having with datetime as the set index.
    cs_data : pandas.Dataframe
        DataFrame with POA based on clearsky values. Column name = 'G'
    threshold : int, optional
        The values below which the data is filtered out. The default is 0.

    Returns
    -------
    pandas.Dataframe
        Filtered dataframe

    '''
    df = data.copy()
    df1 = cs_data.copy()
    # Get timestamp corresponding to solar-hours i.e  G > 0
    day_df = df1[df1 > threshold].dropna(how="all")
    # Filtered dataframe
    df = df[df.index.isin(day_df.index)]
    return df
