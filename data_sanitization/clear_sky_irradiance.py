# -*- coding: utf-8 -*-
"""
Created on Tue Dec 21 08:05:37 2021

@author: Krithika
"""

import pandas as pd
from pvlib.irradiance import get_total_irradiance
from data_sanitization.site_location_pvlib import get_site_location
from data_input.add_multi_index_level import add_index_curve_level


def cs_transpose(times, site_location, clearsky, general_info, array_info,
                 model_transpose='isotropic', temp_val=12):
    '''
    Function that converts Multiindex dataframe containing clearsky GHI to POA

    Parameters
    ----------
    times : pandas.core.indexes.datetimes.DatetimeIndex
        DESCRIPTION. datetime64[ns] series
    site_location : dict
        DESCRIPTION. Location object from pvlib
    clearsky : pandas.Dataframe
        DESCRIPTION. Dataframe containing clear sky GHI , DNI and DHI
    general_info : Dictionary
         Latitude and Longitude in decimal degree format only
         Timezone in the standard format
         Altitude in meters
    array_info : Dataframe
        Contains the static details of the inverters - Surface tilt and Surface
        azimuth angle(degree).
    model_transpose : string, optional
        DESCRIPTION. Scientific models used to transpose GHI to POA.
        The default is 'isotropic'.
    temp_val : int, optional
        DESCRIPTION. Temperature. The default is 12.

    Returns
    -------
    irradiance : pandas.Dataframe
        DESCRIPTION. Multindex or single index dataframe having transposed GHI

    '''
    solar_position = site_location.get_solarposition(times=times)
    # Translate irradiance to POA
    irradiance = pd.DataFrame([], columns=[])
    # Estimates the POA for each input (in a for loop)
    for surface_tilt, surface_azimuth in zip(
            array_info['surface_tilt'],
            array_info['surface_azimuth']):
        irrads = get_total_irradiance(
            surface_tilt=surface_tilt,
            surface_azimuth=surface_azimuth,
            solar_zenith=solar_position['apparent_zenith'],
            solar_azimuth=solar_position['azimuth'],
            dni=clearsky['dni'],
            ghi=clearsky['ghi'],
            dhi=clearsky['dhi'],
            model=model_transpose)
        if irradiance.empty:
            irradiance = pd.DataFrame(irrads['poa_global'], index=times)
        else:
            irradiance = pd.concat([irradiance, pd.DataFrame(
                irrads['poa_global'],
                index=times)],
                axis=1)
    # The column names are included in the same order as in the array_info
    irradiance.columns = add_index_curve_level(array_info.index, 'CS_G')
    return irradiance


def clearsky_irradiance(times, general_info, array_info, convertGHI_toPOA=True,
                        model_cs='simplified_solis',
                        model_transpose='isotropic',
                        temp_val=12):
    '''
    Function that generates clear sky GHI data and converts into POA

    Parameters
    ----------
    times : pandas.core.indexes.datetimes.DatetimeIndex
        DESCRIPTION. datetime64[ns] series
    general_info : Dictionary
         Latitude and Longitude in decimal degree format only
         Timezone in the standard format
         Altitude in meters
    array_info : Dataframe
        Contains the static details of the inverters - Surface tilt and Surface
        azimuth angle(degree).
    convertGHI_toPOA : Boolean, optional
        DESCRIPTION. Converts clearsky GHI to POA if condition is True.
        The default is True.
    model_cs : String, optional
        DESCRIPTION. Scientific models used to estimate clear sky.
        The default is 'simplified_solis'.
    model_transpose : string, optional
        DESCRIPTION. Scientific models used to transpose GHI to POA.
        The default is 'isotropic'.
    temp_val : int, optional
        DESCRIPTION. Temperature. The default is 12.

    Returns
    -------
    cs_data : pandas.Dataframe
        DESCRIPTION. Dataframe having the transposed clearsky GHI. Column name
        "CS_G"

    '''
    # Create location object from pvlib
    site_location = get_site_location(
        latitude=general_info['lat'],
        longitude=general_info['long'],
        altitude=general_info['alt'],
        tz=general_info['timezone'])
    # Create clearky data using get_clearsky object from pvlib
    clearsky = site_location.get_clearsky(times=times, model=model_cs)
    # Converts GHI to POA if convertGHI_POA condition holds True
    if convertGHI_toPOA:
        print("Converting Clearsky GHI to Cleay sky POA...")
        cs_data = cs_transpose(times, site_location, clearsky, general_info,
                               array_info, model_transpose=model_transpose,
                               temp_val=temp_val)
    else:
        # Estimating clearky GHI
        cs_data = clearsky['ghi']
        cs_data.columns = ['CS_GHI']
    return cs_data
