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

def get_start_of_night(dt):
	if datetime_is_naive(dt):
		raise TypeError("Datetime must not be naive")

	timezone_chile = pytz.timezone("America/Santiago")
	dt_chile = dt.astimezone(timezone_chile)

	return (dt_chile - timedelta(hours=12)).strftime("%Y-%m-%d")


def get_mjd(dt):
    #From: https://stackoverflow.com/questions/31142181/calculating-julian-date-in-python
    #From: http://aa.usno.navy.mil/faq/docs/JD_Formula.php

    # Ensure correct format
    if not isinstance(dt, datetime):
        raise TypeError('Invalid type for parameter "date" - expecting datetime')
    elif datetime_is_naive(dt):
        raise TypeError("Datetime must not be naive")
    elif dt.year < 1801 or dt.year > 2099:
        raise ValueError('Datetime must be between year 1801 and 2099')

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
