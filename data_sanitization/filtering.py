"""Filtering outliers."""
import pandas as pd
import rdtools


def irradiance_filter(irrad, irrad_low=200, irrad_high=1200):
    """
    Filter POA irradiance readings based on measurement bounds.

    Parameters
    ----------
    irrad : pandas.Series
        Irradiance measurements.
    irrad_low : float, default 200
        The lower bound of acceptable values.
    irrad_high : float, default 1200
        The upper bound of acceptable values.

    Returns
    -------
    irrad_mask: pandas.Series
        Boolean Series of whether the measurements are within the bounds.
    """
    irrad_mask = (irrad > irrad_low) & (irrad < irrad_high)

    return irrad_mask


def multiindex_irradiance_filter(meteo_data, irrad_low=200, irrad_high=1200):
    """
    Filter POA irradiance readings based on measurement bounds.

    Parameters
    ----------
    meteo_data : pandas DataFrame
        DataFrame containing weather information.
    irrad_low : float, default 200
        The lower bound of acceptable values.
    irrad_high : float, default 1200
        The upper bound of acceptable values.

    Returns
    -------
    filter_df: pandas DataFrame
        Filtered DataFrame.
    """
    met_data_1 = meteo_data.filter(like='Inv')
    filter_df = meteo_data[(met_data_1.xs('G', axis=1, level='curve').ge(
        irrad_low)
                             & met_data_1.xs('G', axis=1, level='curve').le(
                                 irrad_high))]

    return filter_df


def current_filter(current, array_info,
                   isc_col='i_sc', no_str_col='number_of_strings'):
    """
    Filter current readings based on the short circuit current.

    Parameters
    ----------
    current: pandas.Series
        Current measurements.
    array_info: pandas DataFrame
        DataFrame containing system information.
    isc_col: string, default 'i_sc'
        Name of the column with Isc information in "array_info".
    no_str_col: String, default 'number_of_strings'
        Name of the column with number of strings information in "array_info".

    Returns
    -------
    current_mask: pandas.Series
        Boolean series with False for each value that is an outlier.

    """
    isc = float(array_info[isc_col])
    no_str = int(array_info[no_str_col])

    # The short circuit current is multiplied by 1.2 to accommodate
    # the maximum threshold of 1200 W/m^2 in the irradiance_filter function.
    # It is then multiplied with the number of strings
    # to get the upper bound.
    current_mask = (current > 0) & (current <= 1.2 * isc * no_str)

    return current_mask


def multiindex_current_filter(inverter_data, array_info):
    """
    Filter current readings on the multi-index dataframe.

    Parameters
    ----------
    inverter_data : pandas DataFrame
        DataFrame containing operational data.
    array_info : pandas DataFrame
        DataFrame containing system information.

    Returns
    -------
    filter_df: pandas DataFrame
        Filtered dataframe.

    """
    inv_data_1 = inverter_data.filter(like='Inv')
    filter_df = inverter_data[(inv_data_1.xs('I', axis=1, level='curve').ge(0)
                               & inv_data_1.xs('I', axis=1, level='curve').le(
                                  1.2 * array_info.xs('i_sc', axis=1)
                                  * array_info.xs('number_of_strings',
                                                  axis=1)))]

    return filter_df


def voltage_filter(voltage, array_info,
                   voc_col='v_oc', mod_x_str_col='modules_per_string'):
    """
    Filter voltage readings based on the open circuit voltage.

    Parameters
    ----------
    voltage : pandas.Series
        Voltage measurements.
    array_info : pandas DataFrame
        DataFrame containing system information.
    voc_col : string, default 'v_oc'
        Name of the column with Voc information in "array_info".
    mod_x_str_col : string, default 'modules_per_string'
        Name of the column with modules per string information in "array_info".

    Returns
    -------
    voltage_mask: pandas.Series
        Boolean series with False for each value that is an outlier.

    """
    # Obtain the variables for calculation
    voc = float(array_info[voc_col])
    mod_x_str = int(array_info[mod_x_str_col].max())

    # The open circuit voltage is multiplied with the number of modules
    # per string to get the upper bound.
    voltage_mask = (voltage > 0) & (voltage <= voc * mod_x_str)

    return voltage_mask


def multiindex_voltage_filter(inverter_data, array_info):
    """
    Filter voltage readings on the multi-index dataframe.

    Parameters
    ----------
    inverter_data : pandas DataFrame
        DataFrame containing operational data.
    array_info : pandas DataFrame
        DataFrame containing system information.

    Returns
    -------
    filter_df: pandas DataFrame
        Filtered dataframe.

    """
    inv_data_1 = inverter_data.filter(like='Inv')
    filter_df = inverter_data[(inv_data_1.xs('V', axis=1, level='curve').ge(0)
                               & inv_data_1.xs('V', axis=1, level='curve').le(
                                   array_info.xs('v_oc', axis=1)
                                   * array_info.xs('modules_per_string',
                                                   axis=1)))]

    return filter_df


def fidelity_check(df_in):
    """
    Remove repetitive rows and duplicate timestamp records.

    Parameters
    ----------
    df_in: pandas.DataFrame
        The input dataframe.

    Returns
    -------
    ret_df: pandas.DataFrame
        The resultant dataframe.
    """
    # Remove repetitive rows
    if df_in.duplicated().sum() == 0:
        print('This dataframe has no duplicated rows.')
    else:
        print('Removing duplicate rows.')
        # Or, is it keep = 'False', deleting all dupes?
        df_in.drop_duplicates(keep='first', inplace=True)

    # Remove duplicate timestamp records
    ret_df = df_in[~df_in.index.duplicated(keep='first')]

    return ret_df


def resampled_df_after_fidelity_check(df_in, resample_freq=None):
    """
    Resamples the dataframe after removal of rows after fidelity check.

    Parameters
    ----------
    df_in: pandas.DataFrame
        The input dataframe.
    resample_freq: str, default None
        The frequency at which the dataframe must be resampled.

    Returns
    -------
    ret_df: pandas.DataFrame
        The resultant dataframe.
    """
    if resample_freq is None:
        freq = pd.infer_freq(df_in.index[:10])

        if freq is None:
            raise ValueError("There should be a discernible frequency.")
        else:
            resample_freq = freq
    ret_df = rdtools.interpolate(df_in, resample_freq)

    return ret_df
