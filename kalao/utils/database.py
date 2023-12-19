#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Nathanaël Restori
"""

import math
import os
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from pprint import pprint

import pandas as pd

from kalao.utils import kalao_time

import yaml
from bson.codec_options import CodecOptions
from pymongo import DESCENDING, MongoClient, UpdateOne
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
}

condition_mapping = {'==': '$ne', '>=': '$lt', '<=': '$gt'}

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
        dt = kalao_time.now()

    return client[kalao_time.get_start_of_night(dt=dt)]


def get_collection_last_update(collection_name, dt=None):
    db = _get_db(dt)

    collection = db.get_collection(collection_name,
                                   codec_options=codec_options)

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
        return datetime.fromtimestamp(0).replace(tzinfo=timezone.utc)


def get(collection_name, keys=None, nb_of_point=1, dt=None):
    db = _get_db(dt)

    collection = db.get_collection(collection_name,
                                   codec_options=codec_options)

    # yapf: disable
    if keys is None:
        cursor = collection.find(
            {},
            {'_id': 0, 'key': 1, 'values': {'$slice': -nb_of_point}},
            sort=[('last_timestamp', DESCENDING)])

    elif isinstance(keys, str):
        cursor = collection.find(
            {'key': keys},
            {'_id': 0, 'key': 1, 'values': {'$slice': -nb_of_point}},
            limit=1)

    else:
        match_list = []
        for key in list(keys):
            match_list.append({'key': key})

        cursor = collection.aggregate([
            {'$match': {'$or': match_list}},
            {'$project': {'_id': 0, 'key': 1, 'values': {'$slice': ['$values', -nb_of_point]}}},
        ])
    # yapf: enable

    data = {}

    if cursor is not None:
        for document in cursor:
            data[document['key']] = document['values']

    return data


def get_time_since_state(collection_name, key, condition='==', value=None,
                         dt=None):
    db = _get_db(dt)

    collection = db.get_collection(collection_name,
                                   codec_options=codec_options)

    if value is None:
        value = '$current.value'

    if condition in condition_mapping:
        cond = {condition_mapping[condition]: ['$$previous.value', value]}
    else:
        return {}

    # yapf: disable
    cursor = collection.aggregate([
        {'$match': {'key': key}},
        {'$project': {'_id': 0, 'key': 1, 'values': 1}},
        {'$addFields': {'current': {'$arrayElemAt': ['$values', -1]}}},
        {'$addFields': {'previous': {'$arrayElemAt': [{'$filter': {'input': '$values', 'cond': cond, 'as': "previous"}}, -1]}}},
        {'$addFields': {'since': {'$arrayElemAt': [{'$filter': {'input': '$values', 'cond': {'$gt': ['$$since.timestamp', '$previous.timestamp']}, 'as': "since"}}, 1]}}},
        {'$project': {'values': 0}},
    ])
    # yapf: enable

    data = {}

    if cursor is not None:
        for document in cursor:
            data[document['key']] = {
                'current': document.get('current'),
                'previous': document.get('previous'),
                'since': document.get('since')
            }

    return data.get(key)


def store(collection_name, data):
    if len(data) == 0:
        return 0

    now_utc = kalao_time.now()

    # If it's a message for a log, also print it
    for key, value in data.items():
        if '_log' in key:
            log_name = key.replace('_log', '').replace('_', ' ').upper()

            print(f'{log_name} | {value}', flush=True)

    db = _get_db(now_utc)

    timestamp = now_utc
    #timestamp = kalao_time.get_isotime(now_utc)
    #timestamp = now_utc.strftime('%Y-%m-%dT%H:%M:%SZ') # ISO 8601: YYYY-MM-DDThh:mm:ssZ
    #timestamp = kalao_time.get_mjd(now_utc)

    if not collection_name in definitions:
        raise KeyError(
            f'Inserting into unknown collection "{collection_name}" in database'
        )

    collection = db.get_collection(collection_name,
                                   codec_options=codec_options)

    update_list = []

    for key in data.keys():
        if not key in definitions[collection_name]['metadata']:
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


def get_all_last(collection_name):
    return get(collection_name,
               definitions[collection_name]['metadata'].keys())


def get_last(collection_name, key=None, max_days=config.Database.max_days):
    """
    Searches for the last record in the database for a certain collection

    :param collection_name: the collection to search in 'obs', 'monitoring_log', 'telemetry_log'
    :param key: optional key to search for the last record of a specific key
    :return: last record
    """

    dt = kalao_time.now()

    data = {}
    day_number = 0

    while data == {} and day_number <= max_days:
        data = get(collection_name, key, 1, dt=dt - timedelta(days=day_number))
        day_number += 1

    if data == {}:
        return {}
    else:
        if key is None:
            key = list(data.keys())[0]

        data = data[key][0]
        data['key'] = key

        return data


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

    appended_df = []

    if dt is None:
        dt = kalao_time.now()

    for day_number in range(days):
        data = get(collection_name, keys, nb_of_point=99999999,
                   dt=dt - timedelta(days=day_number))

        for key in data.keys():
            data[key] = {d['timestamp']: d['value'] for d in data[key]}

        # Construct the DataFrame
        appended_df.append(pd.DataFrame(data, columns=keys))

    # Check if the database is empty for the given days
    if all([df.empty for df in appended_df]):
        df = pd.DataFrame(columns=keys)
        df.index.name = 'timestamp'
    else:
        df = pd.concat(appended_df).sort_index()

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
