#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Nathanaël Restori
"""
import zoneinfo
from datetime import datetime, timedelta, timezone


def datetime_is_naive(dt: datetime) -> bool:
    # From: https://docs.python.org/3/library/datetime.html#determining-if-an-object-is-aware-or-naive
    return dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None


def get_start_of_night(dt: datetime | None = None) -> datetime:
    """
    Get the night date for the time given by dt. By definition a night date is valid from noon to noon the next day in Chilean local time.

    :param dt: datetime object defining the time for which the night-date is requested. By default, returns the current night date.
    :return: String object containing the night-date in YYYY-MM-DDD format.
    """

    if dt is None:
        dt = datetime.now(timezone.utc)
    elif datetime_is_naive(dt):
        raise Exception('Naive datetimes are not supported')

    timezone_chile = zoneinfo.ZoneInfo('America/Santiago')
    dt_chile = dt.astimezone(timezone_chile)

    if dt_chile.hour < 12:
        return dt_chile.replace(hour=12, minute=0, second=0,
                                microsecond=0) + timedelta(days=-1)
    else:
        return dt_chile.replace(hour=12, minute=0, second=0, microsecond=0)


def get_night_str(dt: datetime | None = None) -> str:
    """
    Get the night date for the time given by dt. By definition a night date is valid from noon to noon the next day in Chilean local time.

    :param dt: datetime object defining the time for which the night-date is requested. By default, returns the current night date.
    :return: String object containing the night-date in YYYY-MM-DDD format.
    """

    return get_start_of_night(dt).strftime('%Y-%m-%d')


def utc_millis_str(dt: datetime | None = None) -> str:
    if dt is None:
        dt = datetime.now(timezone.utc)
    elif datetime_is_naive(dt):
        raise Exception('Naive datetimes are not supported')

    return dt.astimezone(timezone.utc).replace(tzinfo=None).isoformat(
        timespec="milliseconds")
