#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Nathanaël Restori
"""

import math
import os
from collections.abc import KeysView
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from pprint import pprint

import numpy as np
import pandas as pd

from kalao.utils import ktime

import yaml
from bson.codec_options import CodecOptions
from pymongo import DESCENDING, TEXT, MongoClient, UpdateOne
from pymongo.errors import BulkWriteError

import config

definitions = {
    'obs': {
        'path': config.kalao_ics_path / "definitions/db_obs.yml"
    },
    'monitoring': {
        'path': config.kalao_ics_path / "definitions/db_monitoring.yml"
    },
    'telemetry': {
        'path': config.kalao_ics_path / "definitions/db_telemetry.yml"
    },
    'logs': {
        'path': config.kalao_ics_path / "definitions/db_logs.yml"
    },
}

condition_mapping = {
    '==': '$ne',
    '!=': '$eq',
    '>=': '$lt',
    '>': '$lte',
    '<=': '$gt',
    '<': '$gte'
}

codec_options = CodecOptions(tz_aware=True, tzinfo=timezone.utc)


def forked():
    global client

    client = None


def _get_db(dt=None):
    global client

    if client is None:
        client = MongoClient(host=config.Database.ip,
                             port=config.Database.port)

    # If dt is None, get db for today, otherwise get db for the day/night specified by dt
    if dt is None:
        dt = datetime.now(timezone.utc)

    return client[ktime.get_night_str(dt=dt)]


def _get_collection(db, collection_name):
    collection = db.get_collection(collection_name,
                                   codec_options=codec_options)
    collection.create_index([('key', TEXT)], background=True)

    return collection


def get_collection_last_update(collection_name):
    dt = datetime.now(timezone.utc)
    day = 0

    while day <= config.Database.max_days:
        db = _get_db(dt - timedelta(days=day))
        collection = _get_collection(db, collection_name)

        # yapf: disable
        cursor = collection.find(
            {},
            {'_id': 0, 'last_timestamp': 1},
            sort=[('last_timestamp', DESCENDING)],
            limit=1)
        # yapf: enable

        try:
            return cursor[0]['last_timestamp']
        except (IndexError, KeyError):
            pass

        day += 1

    return datetime.fromtimestamp(0, tz=timezone.utc)


def get(collection_name, keys=None, nb_of_point=1, dt=None, days=None,
        at=None):
    day = 0
    data = {}

    if dt is None:
        if at is None:
            dt = datetime.now(timezone.utc)
        else:
            dt = at

    if days is None:
        days = config.Database.max_days

    # Convert dict of key to list
    if isinstance(keys, KeysView):
        keys = list(keys)

    if at is None:
        # Projection used for values array
        if np.isinf(nb_of_point):
            values_projection_find = values_projection_aggregate = 1
        else:
            values_projection_find = {'$slice': -nb_of_point}
            values_projection_aggregate = {'$slice': ['$values', -nb_of_point]}
    else:
        # Filtering used on values array
        values_filter = {
            '$filter': {
                'input': '$values',
                'cond': {
                    '$lte': ['$$this.timestamp', at]
                }
            }
        }

        # Projection used on values array
        if np.isinf(nb_of_point):
            values_projection_find = values_projection_aggregate = values_filter
        else:
            values_projection_find = values_projection_aggregate = {
                '$slice': [values_filter, -nb_of_point]
            }

    while day <= days:
        db = _get_db(dt - timedelta(days=day))
        collection = _get_collection(db, collection_name)

        # yapf: disable
        if keys is None:
            if at is None:
                # We want the nb_of_point last value(s)
                filter = {}
                projection = {'_id': 0, 'key': 1, 'values': values_projection_find}
            else:
                # We want the nb_of_point last value(s) before timestamp
                filter = {'values.timestamp': {'$lte': at}}
                projection = {'_id': 0, 'key': 1, 'values': values_projection_find}

            cursor = collection.find(filter, projection,
                                     sort=[('last_timestamp', DESCENDING)])

        elif isinstance(keys, str):
            if at is None:
                # We want the nb_of_point last value(s)
                filter = {'key': keys}
                projection = {'_id': 0, 'key': 1, 'values': values_projection_find}
            else:
                # We want the nb_of_point last value(s) before timestamp
                filter = {'key': keys, 'values.timestamp': {'$lte': at}}
                projection = {'_id': 0, 'key': 1, 'values': values_projection_find}

            cursor = collection.find(filter, projection, limit=1)

        elif isinstance(keys, list):
            match_list = []
            for key in list(keys):
                match_list.append({'key': key})

            if at is None:
                # We want the nb_of_point last value(s)
                pipeline = [
                    {'$match': {'$or': match_list}},
                    {'$project': {'_id': 0, 'key': 1, 'values': values_projection_aggregate}},
                ]
            else:
                # We want the nb_of_point last value(s) before timestamp
                pipeline = [
                    {'$match': {'$and': [{'$or': match_list}, {'values.timestamp': {'$lte': at}}]}},
                    {'$project':  {'_id': 0, 'key': 1, 'values': values_projection_aggregate}},
                ]

            cursor = collection.aggregate(pipeline)

        else:
            raise TypeError(f'Unsupported type {type(keys)} for keys')
        # yapf: enable

        if cursor is not None:
            for document in cursor:
                key = document['key']

                if key not in data:
                    data[key] = []

                document['values'].reverse()
                data[key] += document['values']

                if isinstance(keys, list) and len(data[key]) >= nb_of_point:
                    if len(data[key]) > nb_of_point:
                        data[key] = data[key][:nb_of_point]

                    keys.remove(key)

        # Check if we gathered the correct number of points
        if keys is None and data != {}:
            return data
        elif isinstance(keys, str) and len(data.get(keys, [])) >= nb_of_point:
            if len(data[keys]) > nb_of_point:
                data[keys] = data[keys][:nb_of_point]
            return data
        elif isinstance(keys, list) and len(keys) == 0:
            return data

        day += 1

    return data


def get_time_since_state(collection_name, key, condition='==', value=None):
    dt = datetime.now(timezone.utc)
    day = 0
    data = {}

    if value is None:
        value = '$current.value'

    if condition in condition_mapping:
        cond = {condition_mapping[condition]: ['$$this.value', value]}
    else:
        return {}

    while 'previous' not in data and day <= config.Database.max_days:
        current = data.get('current', {'$arrayElemAt': ['$values', -1]})

        db = _get_db(dt - timedelta(days=day))
        collection = _get_collection(db, collection_name)

        # yapf: disable
        cursor = collection.aggregate([
            {'$match': {'key': key}},
            {'$project': {'_id': 0, 'key': 1, 'values': 1}},
            {'$addFields': {'current': current}},
            {'$addFields': {'previous': {'$arrayElemAt': [{'$filter': {'input': '$values', 'cond': cond}}, -1]}}},
            {'$addFields': {'since': {'$arrayElemAt': [{'$filter': {'input': '$values', 'cond': {'$gt': ['$$this.timestamp', '$previous.timestamp']}}}, 0]}}},
            {'$project': {'values': 0}},
        ])
        # yapf: enable

        try:
            # Note: document will only contain current and since if no previous is found for this night (previous in another night, since will the first record of the night)
            # Note: document will only contain current and previous if no since is found for this night (since in another night, previous will the last record of the night)
            document = cursor.next()

            if 'current' in document:
                data['current'] = document['current']

            if 'previous' in document:
                data['previous'] = document['previous']

            if 'since' in document:
                data['since'] = document['since']
        except StopIteration:
            pass

        day += 1

    return data


def store(collection_name, data):
    if len(data) == 0:
        return 0

    timestamp = datetime.now(timezone.utc)

    db = _get_db(timestamp)

    if not collection_name in definitions:
        raise KeyError(
            f'Inserting into unknown collection "{collection_name}" in database'
        )
    elif collection_name == 'logs':
        raise KeyError(f'Use store_log to store logs')

    collection = _get_collection(db, collection_name)

    update_list = []

    for key in data.keys():
        if key not in definitions[collection_name]['metadata']:
            raise KeyError(f'Inserting unknown key "{key}" in database')

        if isinstance(data[key], Enum):
            data[key] = data[key].value
        elif isinstance(data[key], Path):
            data[key] = str(data[key])

        # yapf: disable
        update_list.append(UpdateOne(
            {'key': key},
            {
                '$push': {'values': {'value': data[key], 'timestamp': timestamp}},
                '$inc': {'count': 1},
                '$set': {'last_timestamp': timestamp},
            },
            upsert = True
        ))
        # yapf: enable

    try:
        # Use Unordered Bulk Write, to maximise number of keys written in case of failure
        # (only keys with a failure will be skipped)
        collection.bulk_write(update_list, ordered=False)
    except BulkWriteError as bwe:
        print('[ERROR] Write to database failed')
        pprint(bwe.details)
        return -1

    return 0


def store_log(name, level, message):
    timestamp = datetime.now(timezone.utc)

    db = _get_db(timestamp)
    collection = _get_collection(db, 'logs')

    name += '_log'

    if name not in definitions['logs']['metadata']:
        raise KeyError(f'Inserting unknown log "{name}" in database')

    # yapf: disable
    collection.update_one(
        {'key': name},
        {
            '$push': {'messages': {'message': message, 'level': level.value, 'timestamp': timestamp}},
            '$inc': {'count': 1},
            '$set': {'last_timestamp': timestamp},
        },
        upsert = True
    )
    # yapf: enable

    return 0


def get_all_last(collection_name):
    return get(collection_name,
               definitions[collection_name]['metadata'].keys())


def get_last(collection_name, key=None):
    """
    Searches for the last record in the database for a certain collection

    :param collection_name: the collection to search in
    :param key: optional key to search for the last record of a specific key
    :return: last record
    """

    data = get(collection_name, key)

    try:
        if key is None:
            key = list(data.keys())[0]

        data = data[key][0]
        data['key'] = key

        return data
    except (IndexError, KeyError):
        return {}


def get_last_value(collection_name, key=None):
    return get_last(collection_name, key).get('value')


def get_last_time(collection_name, key=None):
    return get_last(collection_name, key).get('timestamp')


def read_mongo_to_pandas_by_timestamp(collection_name, dt_start, dt_end,
                                      keys=None, sampling=None):
    """
    Read from Mongo and Store into DataFrame by timestamp

    :param dt_start:
    :param dt_end:
    :param collection_name:
    :param sampling:
    :return:
    """

    dt_range = dt_end - dt_start
    days = math.ceil(dt_range.days) + 1

    df = read_mongo_to_pandas(collection_name, keys, dt_end, days, sampling)

    return df[(df.index >= dt_start) & (df.index <= dt_end)]


def read_mongo_to_pandas(collection_name, keys=None, dt=None, days=1,
                         sampling=None):
    """
    Read from Mongo and Store into DataFrame by date

    :param dt:
    :param days:
    :param collection_name:
    :param sampling:
    :return:
    """

    if keys is None:
        keys = definitions[collection_name]['metadata'].keys()

    if dt is None:
        dt = datetime.now(timezone.utc)

    data_db = get(collection_name, keys, nb_of_point=np.inf, dt=dt, days=days)

    data_df = {}
    for key in data_db.keys():
        data_df[key] = {d['timestamp']: d['value'] for d in data_db[key]}

    # Construct the DataFrame
    df = pd.DataFrame(data_df, columns=keys)
    df.index.name = 'timestamp'

    # Downsample using temporal binning
    if sampling is not None and len(df) > sampling:
        time_step = ((df.index[-1] - df.index[0]) / sampling)
        df = df.resample(time_step).mean()

    return df


for name in definitions:
    with open(definitions[name]['path']) as file:
        definitions[name]['metadata'] = yaml.safe_load(file)

client = None
os.register_at_fork(after_in_child=forked)
