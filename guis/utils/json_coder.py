import json
from datetime import datetime

import numpy as np
import pandas as pd


class KalAOJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return {'_type': 'datetime', 'value': obj.isoformat()}

        elif isinstance(obj, pd.DataFrame):
            return {'_type': 'DataFrame', 'value': obj.to_json()}

        elif isinstance(obj, np.ndarray):
            if np.ma.is_masked(obj):
                return {
                    '_type': 'ndarray_masked',
                    'data': obj.data.tolist(),
                    'mask': obj.mask.tolist(),
                    'fill_value': obj.fill_value,
                    'shape': list(obj.shape)
                }
            else:
                return {
                    '_type': 'ndarray',
                    'data': obj.tolist(),
                    'shape': list(obj.shape)
                }

        else:
            return json.JSONEncoder.default(self, obj)


class KalAOJSONDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        super().__init__(object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        if '_type' not in obj:
            return obj

        match obj['_type']:
            case 'datetime':
                return datetime.fromisoformat(obj['value'])

            case 'DataFrame':
                return pd.read_json(obj['value'])

            case 'ndarray':
                return np.array(obj['data']).reshape(obj['shape'])

            case 'ndarray_masked':
                return np.ma.array(obj['data'], mask=obj['mask'],
                                   fill_value=obj['fill_value']).reshape(
                                       obj['shape'])

            case _:
                return obj
