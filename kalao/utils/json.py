import json
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

from kalao.definitions.dataclasses import (CalibrationPose, ObservationBlock,
                                           Template)
from kalao.definitions.enums import TemplateID


class KalAOJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return {'_type': 'datetime', 'value': obj.isoformat()}

        elif isinstance(obj, pd.DataFrame):
            return {'_type': 'DataFrame', 'value': obj.to_json()}

        elif isinstance(obj, np.ma.masked_array):
            return {
                '_type': 'ndarray_masked',
                'data': obj.data.tolist(),
                'mask': obj.mask.tolist(),
                'fill_value': obj.fill_value,
                'shape': list(obj.shape)
            }

        elif isinstance(obj, np.ndarray):
            return {
                '_type': 'ndarray',
                'data': obj.tolist(),
                'shape': list(obj.shape)
            }

        elif isinstance(obj, CalibrationPose):
            return {
                '_type': 'CalibrationPose',
                'template': obj.template,
                'filter': obj.filter,
                'exposure_time': obj.exposure_time,
                'median': obj.median,
                'status': obj.status,
                'error_text': obj.error_text
            }

        elif isinstance(obj, ObservationBlock):
            return {
                '_type': 'ObservationBlock',
                'tplno': obj.tplno,
            }

        elif isinstance(obj, Template):
            return {
                '_type': 'Template',
                'id': {
                    '_type': 'TemplateID',
                    'value': obj.id.value
                },
                'start': obj.start,
                'observation_block': obj.observation_block,
                'nexp': obj.nexp,
                'expno': obj.expno,
            }

        elif isinstance(obj, TemplateID):
            return {
                '_type': 'TemplateID',
                'value': obj.value,
            }

        else:
            return json.JSONEncoder.default(self, obj)


class KalAOJSONDecoder(json.JSONDecoder):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
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

            case 'CalibrationPose':
                return CalibrationPose(template=obj['template'],
                                       filter=obj['filter'],
                                       exposure_time=obj['exposure_time'],
                                       median=obj['median'],
                                       status=obj['status'],
                                       error_text=obj['error_text'])
            case 'ObservationBlock':
                return ObservationBlock(tplno=obj['tplno'])

            case 'Template':
                return Template(id=obj['id'], start=obj['start'],
                                observation_block=obj['observation_block'],
                                nexp=obj['nexp'], expno=obj['expno'])

            case 'TemplateID':
                return TemplateID(obj['value'])

            case _:
                return obj
