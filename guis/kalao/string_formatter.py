from string import Formatter

import numpy as np


class KalAOFormatter(Formatter):
    def format_field(self, value, format_spec):
        if isinstance(value, float) and np.isnan(value):
            return '--'
        else:
            return super().format_field(value, format_spec)
