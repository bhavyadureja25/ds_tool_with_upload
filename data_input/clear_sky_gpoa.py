# -*- coding: utf-8 -*-
"""
This method creates a irradiance clear-sky curve in the PoA
@author: DorianGuzman
"""

import pandas as pd
from pvlib import location, irradiance


def get_clearsky_gpoa(times, latitude, longitude, altitude,
                      surface_tilt, surface_azimuth, tz='UTC'):
    """
    This function creates a clear-sky curve and transpose it into a given
    plane defined by the tilt and azimuth angles. The functio uses PVLib
    library, therefore location is needed.

    Parameters
    ----------
    times : Pandas Datetime index
        Pandas Datetime index.
    latitude : Float
        Latitude of the system given in float.
    longitude : Float
        Longitude of the system given in float.
    altitude : Float
        Elevation with restect of the sea level in m. Given in float.
    surface_tilt : Float
        Tilt angle of the plane of array. Given in degrees.
    surface_azimuth : Float
        Azimuth angle of the plane of array. Given in degrees.
    tz : String
        Timezone of the location given in string.
        The default is 'UTC'. If the times are not given in UTC, please
        specify a timezone.

    Returns
    -------
    csky_gpoa : Pandas DataFrame
        Pandas DataFrame with a column named "csky_gpoa".

    """
    # Calling functions to create the irradiance clear-sky curve
    # Create location object from pvlib
    site_location = get_site_location(
        latitude=latitude,
        longitude=longitude,
        altitude=altitude,
        tz=tz)
    # based on the location object it creates a clear sky curve and transpose
    # it
    csky_gpoa = get_irradiance(
        surface_tilt=surface_tilt,
        surface_azimuth=surface_azimuth,
        site_location=site_location,
        times=times)
    return csky_gpoa


def get_site_location(latitude, longitude, altitude, tz):
    """
    Creates a PVLib location object.

    Parameters
    ----------
    latitude : Float
        Latitude of the system given in float.
    longitude : Float
        Longitude of the system given in float.
    altitude : Float
        Elevation with restect of the sea level in m. Given in float.
    tz : String
        Timezone of the location fiven in string.

    Returns
    -------
    site_location : PVLib object
        Returns a location object from PVLib Library.

    """
    # set the location and the time zone for the PV system based on PVLib
    site_location = location.Location(
        latitude=latitude,
        longitude=longitude,
        altitude=altitude,
        tz=tz)
    return site_location


def get_irradiance(times, surface_tilt, surface_azimuth, site_location,
                   model='simplified_solis'):
    """
    Creates a Clear-sky curve basedon the location object and transpose it
    to the plane of array given.

    Parameters
    ----------
    times : Pandas Datetime index
        Pandas Datetime index.
    surface_tilt : Float
        Tilt angle of the plane of array. Given in degrees.
    surface_azimuth : Float
        Azimuth angle of the plane of array. Given in degrees.
    site_location : PVLib object
        Returns a location object from PVLib Library.
    model : String, optional
        Model to be used to create the clear-sky curve.
        The default is 'simplified_solis'.

    Returns
    -------
    Pandas DataFrame
        Pandas DataFrame with a column named "csky_gpoa".

    """
    # Generate clearsky data using the simplified_solis model,
    # The get_clearsky method returns a dataframe with values for GHI, DNI,
    # and DHI
    clearsky = site_location.get_clearsky(times=times,
                                          model=model)
    # Get solar azimuth and zenith to pass to the transposition function
    solar_position = site_location.get_solarposition(times=times)
    # Use the get_total_irradiance function to transpose the GHI to POA
    POA_irradiance = irradiance.get_total_irradiance(
        surface_tilt=surface_tilt,
        surface_azimuth=surface_azimuth,
        dni=clearsky['dni'],
        ghi=clearsky['ghi'],
        dhi=clearsky['dhi'],
        solar_zenith=solar_position['apparent_zenith'],
        solar_azimuth=solar_position['azimuth'])
    # Return DataFrame with only G POA
    return pd.DataFrame({'csky_gpoa': POA_irradiance['poa_global']})
