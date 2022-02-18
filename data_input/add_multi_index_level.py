"""
The notebook helps to add another level to a multi-indexed dataframe.

@author: DurejaBhavya
"""

import pandas as pd


def add_index_curve_level(old_index, curve):
    """
    This function helps to add new index level to the dataframe converting it
    into a multi-index dataframe.

    Parameters
    ----------
    old_index : list of str
        A list of existing column names of the dataframe.
    curve : Str
        The name of the level to be used to create the new level.
    Returns
    -------
    new_index : List of string
        A list of new column names with a added new index level.
    """

    old_index_df = old_index.to_frame()
    old_index_df.insert(0, 'curve', len(old_index) * [curve])
    new_index_names = list(old_index.names)
    new_index_names.insert(0, 'curve')
    new_index = pd.MultiIndex.from_frame(old_index_df, names=new_index_names)
    return new_index
