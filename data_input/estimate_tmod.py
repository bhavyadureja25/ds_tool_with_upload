"""
This file calculates Module Temperature using Irradiance and Ambient
temperature.

@author: DurejaBhavya
"""

import math
import pandas as pd
from data_input.add_multi_index_level import add_index_curve_level


def estimate_module_temperature(df, irr_str, tamb_str='Tamb'):
    """
    This function helps to estimate Module Temperature using Sandia
    Module Temperature Model.

     # Sandia Module Temperature Model

    # https://pvpmc.sandia.gov/modeling-steps/2-dc-module-iv/module-
    temperature/sandia-module-temperature-model/ )

    Parameters
    ----------
    meteo_data: Pandas Dataframe
        Dataframe with Irradiance values
    irr_str: string
        Irradiance column name
    tamb_str: string
        Ambient temperature column name

    Returns
    meteo_data : Pandas dataframe
        dataframe with estimated module temperature column
    """
    # extracting Irradiance and air temperature
    irradiance = df.xs(irr_str, axis=1, level='curve')
    air_temperature = df.xs(tamb_str, axis=1, level='curve')

    # Module type: Glass/cell/polymer sheet # Mount type: Open rack
    a = -3.56
    b = -.0750

    # Module type: Glass/cell/polymer sheet # Mount type: Insulated back
    # a = -2.81
    # b = -.0455

    # estimating module temp using the relationship between Irradiance and Tamb
    est_mod_temp = irradiance * (math.exp(a)) + air_temperature
    # converting est_mod_temp into multi-index dataframe
    est_mod_temp.columns = add_index_curve_level(est_mod_temp.columns, 'Tmod')
    # adding module temperature to meteo_data df
    df = pd.concat([df, est_mod_temp], axis=1)

    return df
