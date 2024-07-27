from string import Formatter

import numpy as np


class KalAOFormatter(Formatter):
    def format_field(self, value, format_spec):
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
