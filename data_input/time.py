"""Obtain UTC for input files."""

import pandas as pd
from tzwhere import tzwhere


def get_tz(latitude, longitude):
    """
    Compute the Time zone from a given latitude and longitude.

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


def get_utc_index(index_in, latitude,
                  longitude, in_utc):
    """
    Convert the time into UTC.

    Parameters
    ----------
    index_in: Pandas DatetimeIndex
        Pandas datetime index.
    latitude: float
        Latitude of the location.
    longitude: float
        Longitude of the location.
    in_utc: bool
        Flag for whether the times are already in UTC time or not.

    Returns
    -------
    ret_index: Pandas index
        Pandas UTC-based date time index.
    """
    if in_utc:
        ret_index = index_in
    else:
        times = index_in.copy()
        start = times[0]
        end = times[-1]

        # freq = pd.Series(times).diff().median().seconds/60
        # freq_str = str(round(freq)) + 'T'
        freq = pd.infer_freq(times)
        timezone_str = get_tz(latitude, longitude)

        # To obtain the UTC time, we find the difference between
        # the current time in our timezone and the UTC time.
        dates = pd.date_range(start=start, end=end, freq=freq,
                              tz=timezone_str)
        df1 = pd.DataFrame({'date1': dates.tz_localize(None)}, index=dates)

        dates = pd.to_datetime(pd.date_range(
            start=start - pd.to_timedelta(1, 'd'),
            end=end + pd.to_timedelta(1, 'd'), freq=freq), utc=True)
        df2 = pd.DataFrame({'date2': dates.tz_localize(None)}, index=dates)

        out = df1.join(df2)
        ret_index = out['date2']

    return ret_index
