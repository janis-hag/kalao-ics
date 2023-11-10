#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Nathanaël Restori
"""

import math
import os
from datetime import timedelta

import pandas as pd

import yaml
from pymongo import DESCENDING, MongoClient, UpdateOne
from pymongo.errors import BulkWriteError

from kalao.utils import kalao_time

#from enum import StrEnum
import kalao_config as config
from kalao_enums import StrEnum

path = os.path.dirname(os.path.abspath(__file__))

definition_names = [
        ('monitoring', path + "/database_definitions/monitoring.yml"),
        ('obs_log', path + "/database_definitions/obs_log.yml"),
        ('telemetry', path + "/database_definitions/telemetry.yml")
]

definitions = {}


def _get_db(client, dt):
    return client[kalao_time.get_start_of_night(dt=dt)]


def _get_data(collection_name, keys=None, nb_of_point=1, dt=None):
    # If dt is None, get db for today, otherwise get db for the day/night specified by dt
    if dt is None:
        dt = kalao_time.now()

    db = _get_db(client, dt)

    collection = db[collection_name]

    # yapf: disable
    if keys is None:
        cursor = collection.find(
            {},
            {'_id': 0, 'key': 1, 'values': {'$slice': -nb_of_point}},
            sort=[('last_timestamp', DESCENDING)],
            limit=1)

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


def _store_data(collection_name, data):
    now_utc = kalao_time.now()

    db = _get_db(client, now_utc)

    timestamp = now_utc
    #timestamp = kalao_time.get_isotime(now_utc)
    #timestamp = now_utc.strftime('%Y-%m-%dT%H:%M:%SZ') # ISO 8601: YYYY-MM-DDThh:mm:ssZ
    #timestamp = kalao_time.get_mjd(now_utc)

    collection = db[collection_name]

    update_list = []

    for key in data.keys():
        if not key in definitions[collection_name]:
            raise KeyError(f'Inserting unknown key "{key}" in database')

        if isinstance(data[key], StrEnum):
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
        collection.bulk_write(update_list, ordered=False)
    except BulkWriteError as bwe:
        print('ERROR: write to database failed')
        print(bwe.details)
        return -1

    return 0


def get_monitoring(keys, nb_of_point=1, dt=None):
    return _get_data('monitoring', keys, nb_of_point, dt=dt)


def get_obs_log(keys, nb_of_point=1, dt=None):
    return _get_data('obs_log', keys, nb_of_point, dt=dt)


def get_telemetry(keys, nb_of_point=1, dt=None):
    return _get_data('telemetry', keys, nb_of_point, dt=dt)


def store_monitoring(data):
    return _store_data('monitoring', data)


def store_obs_log(data):
    return _store_data('obs_log', data)


def store_telemetry(data):
    return _store_data('telemetry', data)


def get_all_last_monitoring():
    return _get_data('monitoring', definitions['monitoring'].keys())


def get_all_last_obs_log():
    return _get_data('obs_log', definitions['obs_log'].keys())


def get_all_last_telemetry():
    return _get_data('telemetry', definitions['telemetry'].keys())


def get_last_record(collection_name, key=None,
                    max_days=config.Database.max_days):
    """
    Searches for the last record in the database for a certain collection

    :param collection_name: the collection to search in 'obs_log', 'monitoring_log', 'telemetry_log'
    :param key: optional key to search for the last record of a specific key
    :return: last record
    """

    dt = kalao_time.now()

    data = {}
    day_number = 0

    while data == {} and day_number <= max_days:
        data = _get_data(collection_name, key, 1,
                         dt=dt - timedelta(days=day_number))
        day_number += 1

    if data == {}:
        return {}
    else:
        if key is None:
            key = list(data.keys())[0]

        return data[key][0]


def get_last_record_value(
        collection_name,
        key=None,
):
    return get_last_record(collection_name, key).get('value')


def get_last_record_time(collection_name, key=None):
    return get_last_record(collection_name, key).get('timestamp')


def read_mongo_to_pandas_by_timestamp(dt_start, dt_end,
                                      collection_name='monitoring',
                                      sampling=None):
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

    df = read_mongo_to_pandas(dt_end, days, collection_name, sampling)

    return df[(df.index >= dt_start) & (df.index <= dt_end)]


def read_mongo_to_pandas(dt=None, days=1, collection_name='monitoring',
                         sampling=None):
    """
    Read from Mongo and Store into DataFrame by date

    :param dt:
    :param days:
    :param collection_name:
    :param sampling:
    :return:
    """

    appended_df = []

    if dt is None:
        dt = kalao_time.now()

    for day_number in range(days):
        data = _get_data(collection_name, definitions[collection_name].keys(),
                         nb_of_point=99999999,
                         dt=dt - timedelta(days=day_number))

        for key in data.keys():
            data[key] = {d['timestamp']: d['value'] for d in data[key]}

        # Construct the DataFrame
        appended_df.append(
                pd.DataFrame(data,
                             columns=definitions[collection_name].keys()))

    # Check if the database is empty for the given days
    if all([df.empty for df in appended_df]):
        df = pd.DataFrame(columns=definitions[collection_name].keys(),
                          index=[0])
    else:
        df = pd.concat(appended_df).sort_index()

    # Downsample using temporal binning
    if sampling is not None and len(df) > sampling:
        time_step = ((df.index[-1] - df.index[0]) / sampling)
        df = df.resample(time_step).mean()

    df['timestamp'] = df.index

    return df


for def_name, def_yaml in definition_names:
    with open(def_yaml) as file:
        definitions[def_name] = yaml.safe_load(file)

client = MongoClient(host=config.Database.ip, port=config.Database.port)
