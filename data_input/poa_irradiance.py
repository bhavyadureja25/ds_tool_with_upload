# -*- coding: utf-8 -*-
"""
Created on Mon Dec 18 08:18:58 2021

@author: Krithika
"""

import pandas as pd
from pvlib.irradiance import erbs
from pvlib.irradiance import dirint
from pvlib.location import Location
from pvlib.irradiance import aoi_projection
from pvlib.irradiance import clearness_index
from pvlib.irradiance import get_extra_radiation
from pvlib.irradiance import get_total_irradiance


def transpose_irradiance(meteo_data, general_info, array_info,
                         poa_model='isotropic'):
    '''
    The function calculates the plane of array (POA) using the measured GHI
    values for each datetime instance
    Parameters
    ----------
    meteo_data : Dataframe
        MultiIndex dataframe having GHI values(Column name GHI) with datetime
        as the set index.
    general_info : Dictionary
         Latitude and Longitude in decimal degree format only
         Timezone in the standard format
         Altitude in meters
    array_info : Dataframe
        Contains the static details of the inverters - Surface tilt and Surface
        azimuth angle(degree)

    Returns
    -------
    meteo_data_transpose : Dataframe
        Returns inputwise POA

    '''
    times = meteo_data.index
    ghi = meteo_data.xs('GHI', axis=1, level='curve').iloc[:, 0].values
    location = Location(general_info['lat'], general_info['long'],
                        general_info['timezone'], general_info['alt'])
    # Calculate solar position
    ephem_df = location.get_solarposition(times)
    # Decompose GHI into DNI and DHI
    data = erbs(ghi, ephem_df['zenith'], times)
    meteo_data_transpose = meteo_data.copy()
    # Translate irradiance to POA
    if isinstance(meteo_data_transpose.columns, pd.MultiIndex):
        for surface_tilt, surface_azimuth, col in zip(
                array_info['surface_tilt'],
                array_info['surface_azimuth'],
                meteo_data.xs('GHI',
                              axis=1,
                              level='curve',
                              drop_level=False).columns):
            irrads = get_total_irradiance(
                surface_tilt=surface_tilt,
                surface_azimuth=surface_azimuth,
                solar_zenith=ephem_df['apparent_zenith'],
                solar_azimuth=ephem_df['azimuth'],
                dni=data['dni'],
                ghi=ghi,
                dhi=data['dhi'],
                model=poa_model)
            meteo_data_transpose.loc[:, col] = irrads['poa_global']
    else:
        irrads = get_total_irradiance(surface_tilt=surface_tilt,
                                      surface_azimuth=surface_azimuth,
                                      solar_zenith=ephem_df['apparent_zenith'],
                                      solar_azimuth=ephem_df['azimuth'],
                                      dni=data['dni'],
                                      ghi=ghi,
                                      dhi=data['dhi'],
                                      model=poa_model)
        meteo_data_transpose = irrads['poa_global']
    return meteo_data_transpose


def get_operational_irradiance(meteo_data, general_info, array_info,
                               poa_model='isotropic'):
    '''
    The function determines the irradiance(POA)
    Parameters
    ----------
    meteo_data : Dataframe
        DESCRIPTION. MultiIndex dataframe having GHI values(Column name GHI)
        with datetime as the set index.
    general_info : Dictionary
        DESCRIPTION. Latitude and Longitude in decimal degree format only
                     Timezone in the standard format
                     Altitude in meters
    array_info : Dataframe
        DESCRIPTION. Contains the static details of the inverters - Surface
        tilt and Surface azimuth angle(degree)
    convertGHI_toPOA : Boolean, optional
        DESCRIPTION. True that the irradiance must be converted from GHI to
        POA. False indicates the irradiance
        is already in POA.
        The default is True

    Returns
    -------
    poa_data : Dataframe
        DESCRIPTION. Returns inputwise POA

    '''
    if general_info['irradiance_type'] == "GHI":
        print("Converting GHI to POA...")
        poa_data = transpose_irradiance(meteo_data, general_info, array_info,
                                        poa_model=poa_model)
    else:
        print("Measured irradiance is already at POA")
        poa_data = meteo_data
    return poa_data
