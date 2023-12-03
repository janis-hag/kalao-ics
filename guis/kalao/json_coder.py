import json
from datetime import datetime

import pandas as pd


class FakeSignal():
    def __init__(self, name, args=None):
        self.name = name
        self.args = args

    def emit(self, *args):
        self.args = args

        return self


class KalAOJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return {"_type": "datetime", "value": obj.isoformat()}

        if isinstance(obj, pd.DataFrame):
            return {"_type": "DataFrame", "value": obj.to_json()}

        if isinstance(obj, FakeSignal):
            return {"_type": "FakeSignal", "name": obj.name, "args": obj.args}

        return json.JSONEncoder.default(self, obj)


class KalAOJSONDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        super().__init__(object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        if '_type' not in obj:
            return obj

        type = obj['_type']

        if type == 'datetime':
            return datetime.fromisoformat(obj['value'])

        if type == 'DataFrame':
            return pd.read_json(obj['value'])

        if type == 'FakeSignal':
            return FakeSignal(obj['name'], obj['args'])

        return obj
