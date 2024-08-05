from string import Formatter
from typing import Any

import numpy as np


class KalAOFormatter(Formatter):
    def format_field(self, value: Any, format_spec: str) -> str:
        if isinstance(value, float):
            if np.isnan(value):
                return '--'
            elif np.isposinf(value):
                return '∞'
            elif np.isneginf(value):
                return '-∞'
            else:
                return super().format_field(value, format_spec)
        else:
            return super().format_field(value, format_spec)
