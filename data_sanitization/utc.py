# -*- coding: utf-8 -*-
"""
This file contains the tools to be used for the UTC awareness.

@author: DorianGuzman
"""
from tzwhere import tzwhere
import pandas as pd


def get_tz(latitude, longitude):
    """
    This function computes the Time zone from a given latitude and longitude.

    Parameters
    ----------
    latitude : Float
        Latitude in float numbers.
    longitude : Float
        Longitude in Float numbers.

    Returns
    -------
    timezone_str : String
        Time zone in described in string.

    """
    # Get the time zone based on the GPS location
    tz = tzwhere.tzwhere()
    timezone_str = tz.tzNameAt(latitude, longitude)
    return timezone_str


def utc_index_shifted(index_in):
    """
    This function detects the UTC values and shifts the index depending on the
    UTC sign. if UTC + the index will be shifted forward and if UTC - the
    index will be shifted backwards.

    Parameters
    ----------
    df_in : Pandas datetime index
        Pandas datetime index.

    Returns
    -------
    ret_index : Pandas index
        Pandas datetime index shifted backwards or forward based on the UTC.

    """
    times = index_in.copy()
    # get the utc as list
    utc_list = times.strftime("%z")
    # get the first element to detect the sign
    element = utc_list[0]
    if '+' in element:
        sign_str = '+'
    else:
        sign_str = '-'
    # get a new list with integers and get the max value of UTC
    utc_list = [int(i.split(sign_str, 1)[1]) for i in utc_list]
    utc_max = max(utc_list)
    utc_max_str = str(utc_max)
    # get the hours and minutes in integers
    hours = int(utc_max_str[:-2])
    minutes = int(utc_max_str[-2:])
    # get total minutes for the pandas offset in minutes
    total_min = ((hours * 60) + minutes) * 2
    # Set the return index including the offset already
    if sign_str == '+':
        ret_index = times - pd.offsets.Minute(total_min)
    else:
        ret_index = times + pd.offsets.Minute(total_min)

    return ret_index


def utc_aware(df_in, tz, datetime_format):
    """
    This function takes a DataFrame with naive timestamps index, and converts
    it to UTC aware based on the tz.

    Parameters
    ----------
    df_in : Panas DataFrame
        Pandas DataFrame with Datetime index.
    tz : String
        Time zone in described in string.
    datetime_format : String
        Format of Datetime index.

    Returns
    -------
    Pandas Datetime index
        Pandas Datetime index with UTC awareness.

    """
    df = df_in.copy()
    df_out = pd.DataFrame()
    df_out['datetime'] = df.index.strftime(datetime_format)
    df_out = pd.to_datetime(df_out.datetime,
                            format=datetime_format,
                            utc=True).dt.tz_convert(tz)
    df_out = pd.DataFrame(df_out.sort_values())
    df_out = df_out.set_index(df_out.datetime).drop(
        "datetime", axis=1)
    df_out.index = utc_index_shifted(
        index_in=df_out.index)

    return df_out.index
