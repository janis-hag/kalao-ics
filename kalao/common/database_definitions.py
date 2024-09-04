from typing import Any

import numpy as np

import yaml

from kalao.common.dataclasses import Alarm
from kalao.common.enums import AlarmLevel

import config

with open(config.kalao_ics_path / 'definitions/db_obs.yaml') as f:
    obs = yaml.safe_load(f)

with open(config.kalao_ics_path / 'definitions/db_monitoring.yaml') as f:
    monitoring = yaml.safe_load(f)

with open(config.kalao_ics_path / 'definitions/db_logs.yaml') as f:
    logs = yaml.safe_load(f)


def check_alarm(key: str, value: Any) -> Alarm:
    metadata = monitoring[key]

    alarm_values = metadata.get('alarm_values', [])
    is_numeric = isinstance(value, float) or isinstance(value, int)

    if value in alarm_values or (is_numeric and np.isnan(value) and
                                 np.isnan(alarm_values).any()):
        return Alarm(level=AlarmLevel.ALARM, condition='==', threshold=value)
    elif is_numeric:
        alarm_range = metadata.get('alarm_range', [np.nan, np.nan])
        warn_range = metadata.get('warn_range', [np.nan, np.nan])

        alarm_min = alarm_range[0]
        alarm_max = alarm_range[1]
        warn_min = warn_range[0]
        warn_max = warn_range[1]

        if value > alarm_max:
            return Alarm(level=AlarmLevel.ALARM, condition='>',
                         threshold=alarm_max)
        elif value < alarm_min:
            return Alarm(level=AlarmLevel.ALARM, condition='<',
                         threshold=alarm_min)
        elif value > warn_max:
            return Alarm(level=AlarmLevel.WARNING, condition='>',
                         threshold=warn_max)
        elif value < warn_min:
            return Alarm(level=AlarmLevel.WARNING, condition='<',
                         threshold=warn_min)
        else:
            return Alarm(level=AlarmLevel.OK, condition='', threshold=np.nan)
    else:
        return Alarm(level=AlarmLevel.OK, condition='', threshold=np.nan)
