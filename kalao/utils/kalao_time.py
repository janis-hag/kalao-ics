#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Nathanaël Restori
"""

import math

from datetime import datetime, timedelta, timezone
import pytz


def datetime_is_naive(d):
    # From: https://docs.python.org/3/library/datetime.html#determining-if-an-object-is-aware-or-naive
    return d.tzinfo is None or d.tzinfo.utcoffset(d) is None


def get_start_of_night(dt=None):
    if dt is None:
        dt = now()
    # elif type(dt) is not datetime:
    #     raise TypeError('Invalid type for parameter "date" - expecting datetime')
    # if datetime_is_naive(dt):
    #     raise TypeError("Datetime must not be naive")

    check_time_format(dt)

    timezone_chile = pytz.timezone("America/Santiago")
    dt_chile = dt.astimezone(timezone_chile)

    return (dt_chile - timedelta(hours=12)).strftime("%Y-%m-%d")


def get_mjd(dt):
    #From: https://stackoverflow.com/questions/31142181/calculating-julian-date-in-python
    #From: http://aa.usno.navy.mil/faq/docs/JD_Formula.php

    # # Ensure correct format
    # if not isinstance(dt, datetime):
    #     raise TypeError('Invalid type for parameter "date" - expecting datetime')
    # elif datetime_is_naive(dt):
    #     raise TypeError("Datetime must not be naive")
    # elif dt.year < 1801 or dt.year > 2099:
    #     raise ValueError('Datetime must be between year 1801 and 2099')

    check_time_format(dt)

    # Perform the calculation
    dt_utc = dt.astimezone(timezone.utc)

    julian_datetime = 367 * dt_utc.year - int((7 * (dt_utc.year + int((dt_utc.month + 9) / 12.0))) / 4.0) \
                                        + int((275 * dt_utc.month) / 9.0) \
                                        + dt_utc.day \
                                        + 1721013.5 \
                                        + (dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / math.pow(60, 2)) / 24.0 \
                                        - 0.5 * math.copysign(1, 100 * dt_utc.year + dt_utc.month - 190002.5) \
                                        + 0.5 \
                                        - 24000.5

    return julian_datetime

def check_time_format(dt):
    '''
    Verify that datetime format is correct. Return the dt object if it is correct.

    :param dt: datetime object to verify
    :return: dt object
    '''
    # Ensure correct format
    if not isinstance(dt, datetime):
        raise TypeError('Invalid type for parameter "date" - expecting datetime')
    elif datetime_is_naive(dt):
        raise TypeError("Datetime must not be naive")
    elif dt.year < 1801 or dt.year > 2099:
        raise ValueError('Datetime must be between year 1801 and 2099')

    return dt

def get_isotime(now_time=None):
    """
    Takes an datetime object or otherwise the current UTC time and returns a string in ISO 8601 format format such as
    YYYY-MM-DDTHH.MM.SS.mmm = %Y-%m-%dT%H:%M:%S[.fff]
    leaving out the UTC offset information.

    :param now_time: datetime object
    :return: datetime string in iso format
    """

    if now_time is None:
        return now().replace(tzinfo=None).isoformat(timespec='milliseconds')
    else:
        check_time_format(now_time)
        return now_time.replace(tzinfo=None).isoformat(timespec='milliseconds')

def now():
    """
    Gets the current UTC time as a timezone aware datetime object

    :return: datetime object
    """
    return datetime.now(timezone.utc)
