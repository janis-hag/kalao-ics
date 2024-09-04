#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Nathanaël Restori
"""
import os
import pprint
from collections.abc import KeysView
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from bson.codec_options import CodecOptions
from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.errors import BulkWriteError

from kalao.common import database_definitions
from kalao.common.enums import LogLevel, ReturnCode
from kalao.common.rprint import rprint

import config

condition_mapping = {
    '==': '$ne',
    '!=': '$eq',
    '>=': '$lt',
    '>': '$lte',
    '<=': '$gt',
    '<': '$gte'
}

codec_options = CodecOptions(tz_aware=True, tzinfo=timezone.utc)

client: MongoClient | None = None


def _reset_client() -> None:
    global client

    if client is not None:
        client.close()

    client = MongoClient(host=config.Database.host, port=config.Database.port)

    # client.admin.command('ping')


def _get_collection(collection_name: str) -> Collection:
    db = client['kalao']

    if collection_name in db.list_collection_names():
        collection = db.get_collection(collection_name,
                                       codec_options=codec_options)
    else:
        collection = db.create_collection(
            collection_name,
            codec_options=codec_options,
            timeseries={
                'timeField': 'timestamp',
                'metaField': 'metadata',
                #'granularity': 'minutes', # Set manually below
                'bucketMaxSpanSeconds': 86400,
                'bucketRoundingSeconds': 86400,
            })

    # collection.create_index([('key', TEXT)], background=True)

    return collection


def get_collection_last_update(collection_name: str) -> datetime:
    collection = _get_collection(collection_name)

    document = collection.find_one({}, sort=[('timestamp', DESCENDING)])

    if document is None:
        return datetime.fromtimestamp(0, tz=timezone.utc)
    else:
        return document['timestamp']


def get_last(collection_name: str, key: str) -> dict:
    collection = _get_collection(collection_name)

    document = collection.find_one({'metadata.key': key},
                                   sort=[('timestamp', DESCENDING)])

    if document is None:
        return {
            'timestamp': None,
            'value': None,
        }
    else:
        return {
            'timestamp': document['timestamp'],
            'value': document['value'],
        }


def get_last_value(collection_name: str, key: str) -> Any:
    return get_last(collection_name, key)['value']


def get_last_time(collection_name: str, key: str) -> Any:
    return get_last(collection_name, key)['timestamp']


def get_all_last(collection_name: str, keys: list | KeysView | None = None,
                 at: datetime | None = None) -> dict:
    # Convert dict's keys to list
    if isinstance(keys, KeysView):
        keys = list(keys)

    matcher = {}
    if isinstance(keys, list):
        matcher['metadata.key'] = {'$in': keys}
    elif keys is None:
        pass
    else:
        raise TypeError(f'Unsupported type {type(keys)} for keys')

    if at is not None:
        matcher['timestamp'] = {'$lte': at}

    pipeline = []

    if len(matcher) != 0:
        pipeline.append({'$match': matcher})

    pipeline.append({'$sort': {'timestamp': DESCENDING}})

    pipeline.append({
        '$group': {
            '_id': '$metadata.key',
            'timestamp': {
                '$first': '$timestamp'
            },
            'value': {
                '$first': '$value'
            }
        }
    })

    collection = _get_collection(collection_name)

    cursor = collection.aggregate(pipeline)

    data = {}
    for document in cursor:
        data[document['_id']] = {
            'timestamp': document['timestamp'],
            'value': document['value'],
        }

    return data


def read_mongo_to_pandas(collection_name: str, keys: str | list | KeysView |
                         None = None, since: datetime | None = None,
                         until: datetime | None = None,
                         sampling: int | None = None) -> pd.DataFrame:
    # Convert dict's keys to list
    if isinstance(keys, KeysView):
        keys = list(keys)

    matcher = {}
    if isinstance(keys, str):
        matcher['metadata.key'] = keys
    elif isinstance(keys, list):
        matcher['metadata.key'] = {'$in': keys}
    elif keys is None:
        pass
    else:
        raise TypeError(f'Unsupported type {type(keys)} for keys')

    if since is not None or until is not None:
        matcher['timestamp'] = {}

        if since is not None:
            matcher['timestamp']['$gte'] = since

        if until is not None:
            matcher['timestamp']['$lte'] = until

    pipeline = []

    if len(matcher) != 0:
        pipeline.append({'$match': matcher})

    pipeline.append({'$sort': {'timestamp': DESCENDING}})

    collection = _get_collection(collection_name)

    cursor = collection.aggregate(pipeline)

    data_df = {}
    for document in cursor:
        key = document['metadata']['key']

        if key not in data_df:
            data_df[key] = {}

        data_df[key][document['timestamp']] = document['value']

    if isinstance(keys, str):
        keys = [keys]
    elif keys is None:
        keys = data_df.keys()

    # Construct the DataFrame
    df = pd.DataFrame(data_df, columns=keys)
    df.index.name = 'timestamp'

    # Downsample using temporal binning
    if sampling is not None and len(df) > sampling:
        time_step = ((df.index[-1] - df.index[0]) / sampling)
        df = df.resample(time_step).mean()

    return df


def store(collection_name: str, data: dict[str, Any],
          timestamp: datetime = None) -> ReturnCode:
    if len(data) == 0:
        return ReturnCode.DATABASE_OK

    if timestamp is None:
        timestamp = datetime.now(timezone.utc)

    if not hasattr(database_definitions, collection_name):
        raise KeyError(
            f'Inserting into unknown collection "{collection_name}" in database'
        )
    elif collection_name == 'logs':
        raise KeyError('Use store_log to store logs')

    collection = _get_collection(collection_name)

    insert_list = []

    for key, value in data.items():
        if key not in getattr(database_definitions, collection_name):
            raise KeyError(f'Inserting unknown key "{key}" in database')

        if isinstance(value, Enum):
            value = value.value
        elif isinstance(value, Path):
            value = str(value)
        elif isinstance(value, np.int64):
            value = int(value)
        elif isinstance(value, np.float64):
            value = float(value)

        insert_list.append({
            'metadata': {
                'key': key
            },
            'timestamp': timestamp,
            'value': value
        })

    try:
        # Use Unordered Bulk Write, to maximise number of keys written in case of failure
        # (only keys with a failure will be skipped)
        collection.insert_many(insert_list, ordered=False)
    except BulkWriteError as bwe:
        rprint('[ERROR] Write to database failed')
        rprint(pprint.pformat(bwe.details))
        return ReturnCode.DATABASE_ERROR

    return ReturnCode.DATABASE_OK


def store_log(name: str, level: LogLevel, message: str) -> ReturnCode:
    timestamp = datetime.now(timezone.utc)

    collection = _get_collection('logs')

    name += '_log'

    if name not in database_definitions.logs:
        raise KeyError(f'Inserting unknown log "{name}" in database')

    try:
        collection.insert_one({
            'metadata': {
                'key': name
            },
            'timestamp': timestamp,
            'level': level,
            'message': message,
        })
    except BulkWriteError as bwe:
        rprint('[ERROR] Write to database failed')
        rprint(pprint.pformat(bwe.details))
        return ReturnCode.DATABASE_ERROR

    return ReturnCode.DATABASE_OK


def get_time_since_state(collection_name: str, key: str, condition: str = '==',
                         value: str | int | float | None = None
                         ) -> dict[str, Any]:
    if condition not in condition_mapping:
        raise Exception('Unsupported condition')

    collection = _get_collection(collection_name)

    data = {}

    document = collection.find_one({'metadata.key': key},
                                   sort=[('timestamp', DESCENDING)])

    if document is None:
        return data

    data['current'] = {
        'value': document['value'],
        'timestamp': document['timestamp'],
    }

    if value is None:
        value = data['current']['value']

    ##### Find when the condition was not fullfilled

    document = collection.find_one(
        {
            'metadata.key': key,
            'value': {
                condition_mapping[condition]: value
            }
        }, sort=[('timestamp', DESCENDING)])

    if document is None:
        return data
    else:
        data['previous'] = {
            'value': document['value'],
            'timestamp': document['timestamp'],
        }

    ##### Find since when the condition is fullfilled

    document = collection.find_one(
        {
            'metadata.key': key,
            'timestamp': {
                '$gt': data['previous']['timestamp']
            }
        }, sort=[('timestamp', ASCENDING)])

    if document is None:
        return data
    else:
        data['since'] = {
            'value': document['value'],
            'timestamp': document['timestamp'],
        }

    return data


os.register_at_fork(after_in_child=_reset_client)

_reset_client()
