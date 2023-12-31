#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Nathanaël Restori
"""

from pymongo import MongoClient
from pymongo import ASCENDING, DESCENDING

from datetime import datetime, timezone, timedelta
import yaml
import json
import os
import math

import pandas as pd

from kalao.utils import kalao_time
from kalao.cacao import fake_data

path = os.path.dirname(os.path.abspath(__file__))

monitoring_definition_json = path + "/database_definition_monitoring.json"
monitoring_definition_yaml = path + "/database_definition_monitoring.yml"

obs_log_definition_json = path + "/database_definition_obs_log.json"
obs_log_definition_yaml = path + "/database_definition_obs_log.yml"

#telemetry
telemetry_definition_json = path + "/database_definition_telemetry.json"
telemetry_definition_yaml = path + "/database_definition_telemetry.yml"

definition_names = [
        ('monitoring', monitoring_definition_yaml, monitoring_definition_json),
        ('obs_log', obs_log_definition_yaml, obs_log_definition_json),
        ('telemetry', telemetry_definition_yaml, telemetry_definition_json)
]

definitions = {}


def convert_database_definition():
    for def_name, def_yaml, def_json in definition_names:
        with open(def_yaml, 'r') as yaml_in, open(def_json, "w") as json_out:
            yaml_object = yaml.safe_load(yaml_in)
            json.dump(yaml_object, json_out)


def connect_db():
    client = MongoClient("127.0.0.1")
    return client


def get_db(client, dt):
    return client[kalao_time.get_start_of_night(dt=dt)]


def store_monitoring(data):
    return store_data('monitoring', data, definitions['monitoring'])


def store_obs_log(data):
    return store_data('obs_log', data, definitions['obs_log'])


def store_telemetry(data):
    return store_data('telemetry', data, definitions['telemetry'])


def store_data(collection_name, data, definition):
    now_utc = kalao_time.now()

    with connect_db() as client:
        db = get_db(client, now_utc)
        #with get_db(now_utc) as db:

        data['time_utc'] = now_utc
        #data['time_utc'] = kalao_time.get_isotime(now_utc)
        # data['time_utc'] = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ") # ISO 8601: YYYY-MM-DDThh:mm:ssZ
        #data['time_mjd'] = kalao_time.get_mjd(now_utc)

        collection = db[collection_name]

        for key in data.keys():
            if not key in definition:
                raise KeyError(f'Inserting unknown key "{key}" in database')

        insertion_return = collection.insert_one(data)

    #db.close()

    return insertion_return


def get_monitoring(keys, nb_of_point, dt=None):
    return get_data('monitoring', keys, nb_of_point, dt=dt)


def get_obs_log(keys, nb_of_point, dt=None):
    return get_data('obs_log', keys, nb_of_point, dt=dt)


def get_telemetry(keys, nb_of_point, dt=None):
    return get_data('telemetry', keys, nb_of_point, dt=dt)


def get_telemetry_series(realData=True):
    return fake_data.fake_telemetry_series()


def get_data(collection_name, keys, nb_of_point, dt=None):
    # TODO get data from additional day in nb_of_points not reached
    # If dt is None, get db for today, otherwise get db for the day/night specified  by dt
    if dt is None:
        dt = kalao_time.now()

    with connect_db() as client:

        db = get_db(client, dt)

        #collection = db[collection_name]

        data = {}

        for key in keys:
            cursor = db[collection_name].find({key: {
                    '$exists': True
            }}, {
                    'time_utc': True,
                    key: True
            }, sort=[('time_utc', DESCENDING)], limit=nb_of_point)

            data[key] = {'time_utc': [], 'values': []}

            for doc in cursor:
                data[key]['time_utc'].append(doc['time_utc'])
                data[key]['values'].append(doc[key])

    #client.close()

    return data


def get_all_last_monitoring(realData=True):
    return get_monitoring(definitions['monitoring'].keys(), 1)


def get_all_last_obs_log():
    return get_data('obs_log', definitions['obs_log'].keys(), 1, dt=None)


def get_all_last_telemetry(realData=True):
    if realData is False:
        return fake_data.fake_telemetry_for_db()
    return get_data('telemetry', definitions['telemetry'].keys(), 1, dt=None)


def get_latest_record(collection_name, key=None, no_id=True):
    """
    Searches for the last record in the database for a certain collection

    :param collection_name: the collection to search in 'obs_log', 'monitoring_log', 'telemetry_log'
    :param key: optional key to search for the last record of a specific key
    :return: last record
    """

    dt = kalao_time.now()

    latest_record = None
    day_number = 0

    while latest_record is None:
        if key is None:
            last_logs = get_data(collection_name,
                                 definitions[collection_name].keys(), 1,
                                 dt=dt - timedelta(days=day_number))

            if last_logs['time_utc'].get('values'):
                with connect_db() as client:
                    db = get_db(client, dt - timedelta(days=day_number))
                    latest_record = list(
                            db[collection_name].find().limit(1).sort([
                                    ('$natural', -1)
                            ]))[0]

        else:
            with connect_db() as client:
                db = get_db(client, dt - timedelta(days=day_number))
                latest_record = list(db[collection_name].find({
                        key: {
                                "$ne": None
                        }
                }).limit(1).sort([('$natural', -1)]))
                if len(latest_record) == 0:
                    latest_record = None
                else:
                    latest_record = latest_record[0]
                    if no_id:
                        del latest_record['_id']
        day_number += 1

        if day_number > 100:
            break
    #client.close()

    return latest_record


def read_mongo_to_pandas_by_timestamp(dt_start, dt_end, sampling=1500,
                                      collection_name='monitoring'):
    """
    Read from Mongo and Store into DataFrame by timestamp

    :param dt_start:
    :param dt_end:
    :param sampling:
    :param collection_name:
    :return:
    """

    dt_range = dt_end - dt_start
    dt = dt_start
    days = int(math.ceil(dt_range.days)) + 1
    no_id = True
    appended_df = []

    with connect_db() as client:

        for day_number in range(days):
            # Loop of days
            db = get_db(client, dt + timedelta(days=day_number))

            # Make a query to the specific DB and Collection
            #cursor = db[collection].find(query)
            cursor = db[collection_name].find()

            # Expand the cursor and construct the DataFrame
            appended_df.append(pd.DataFrame(list(cursor)))

        # Check if the databse is empty for the given days
        if all([df.empty for df in appended_df]):
            # Search one more day back in time to look for database content
            db = get_db(client, dt + timedelta(days=days))
            df = pd.DataFrame(list(db[collection_name].find()))

            # If it did not succeed return a NaN database with column names
            if df.empty:
                df = pd.DataFrame(
                        columns=list(definitions['monitoring'].keys()),
                        index=[0])
                no_id = False  # Set to False because the '_id' column does not exist in this df

        else:
            df = pd.concat(appended_df).sort_values(by='time_utc',
                                                    ignore_index=True)

        # Delete the _id
        if no_id:
            del df['_id']

    # Downsample using temporal binning
    if sampling < len(df):
        time_step = ((df['time_utc'][-1:] - df['time_utc'][0]) /
                     sampling).iat[0]
        df = df.resample(time_step, on='time_utc').mean()
        #df['time_utc'] = df.index
        df.reset_index(inplace=True)

    return df


def read_mongo_to_pandas(dt=None, days=1, collection_name='monitoring',
                         no_id=True):
    """
    Read from Mongo and Store into DataFrame by date

    :param dt:
    :param days:
    :param collection_name:
    :param no_id:
    :return:
    """

    appended_df = []

    if dt is None:
        dt = datetime.now(timezone.utc)

    # Connect to MongoDB
    with connect_db() as client:

        for day_number in range(days):
            # Loop of days
            db = get_db(client, dt - timedelta(days=day_number))

            # Make a query to the specific DB and Collection
            #cursor = db[collection].find(query)
            cursor = db[collection_name].find()

            # Expand the cursor and construct the DataFrame
            appended_df.append(pd.DataFrame(list(cursor)))

        # Check if the database is empty for the given days
        if all([df.empty for df in appended_df]):
            # Search one more day back in time to look for database content
            db = get_db(client, dt - timedelta(days=days))
            df = pd.DataFrame(list(db[collection_name].find()))

            # If it did not succeed return a NaN database with column names
            if df.empty:
                df = pd.DataFrame(
                        columns=list(definitions['monitoring'].keys()),
                        index=[0])
                no_id = False  # Set to False because the '_id' column does not exist in this df

        else:
            df = pd.concat(appended_df).sort_values(by='time_utc',
                                                    ignore_index=True)

        # Delete the _id
        if no_id:
            del df['_id']

    return df


if __name__ == "__main__":
    print("Converting database definition")
    convert_database_definition()
else:
    for def_name, def_yaml, definition_json in definition_names:
        with open(definition_json) as file:
            definitions[def_name] = json.load(file)
