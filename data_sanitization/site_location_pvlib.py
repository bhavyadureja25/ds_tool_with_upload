from datetime import timedelta
import pandas as pd
import numpy as np

from pvlib.irradiance import clearness_index
from pvlib.irradiance import erbs 
from pvlib.irradiance import dirint
from pvlib.irradiance import get_total_irradiance
from pvlib.irradiance import get_extra_radiation
from pvlib.irradiance import aoi_projection
from pvlib.location import Location
from pvlib import location


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