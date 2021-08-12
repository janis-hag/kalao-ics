#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Nathanaël Restori
"""

from pymongo import MongoClient
from pymongo import ASCENDING, DESCENDING

from datetime import datetime, timezone
import yaml
import json
import os

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

definition_names = [('monitoring', monitoring_definition_yaml, monitoring_definition_json),
                    ('obs_log', obs_log_definition_yaml, obs_log_definition_json),
                    ('telemetry', telemetry_definition_yaml, telemetry_definition_json)]

definitions = {}

for def_name, def_yaml, definition_json in definition_names:
    with open(definition_json) as file:
        definitions[def_name] = json.load(file)


def convert_database_definition():
    for def_name, def_yaml, def_json in definition_names:
        with open(def_yaml, 'r') as yaml_in, open(def_json, "w") as json_out:
            yaml_object = yaml.safe_load(yaml_in)
            json.dump(yaml_object, json_out)


def get_db(dt):
    client = MongoClient("127.0.0.1")
    return client[kalao_time.get_start_of_night(dt=dt)]


def store_monitoring(data):
    return store_data('monitoring', data, definitions['monitoring'])


def store_obs_log(data):
    return store_data('obs_log', data, definitions['obs_log'])


def store_telemetry(data):
    return store_data('telemetry', data, definitions['telemetry'])


def store_data(collection_name, data, definition):
    now_utc = kalao_time.now()
    db = get_db(now_utc)

    data['time_utc'] = now_utc
    #data['time_utc'] = kalao_time.get_isotime(now_utc)
    # data['time_utc'] = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ") # ISO 8601: YYYY-MM-DDThh:mm:ssZ
    #data['time_mjd'] = kalao_time.get_mjd(now_utc)

    collection = db[collection_name]

    for key in data.keys():
        if not key in definition:
            raise KeyError(f'Inserting unknown key "{key}" in database')

    return collection.insert_one(data)


def get_monitoring(keys, nb_of_point, dt=None):
    return get_data('monitoring', keys, nb_of_point, dt=None)


def get_obs_log(keys, nb_of_point, dt=None):
    return get_data('obs_log', keys, nb_of_point, dt=None)


def get_telemetry(keys, nb_of_point, dt=None):
    return get_data('telemetry', keys, nb_of_point, dt=None)


def get_telemetry_series(realData=True):
    return fake_data.fake_telemetry_series()


def get_data(collection_name, keys, nb_of_point, dt=None):
    # If dt is None, get db for today, otherwise get db for the day/night specified  by dt
    if dt is None:
        dt = kalao_time.now()
    db = get_db(dt)

    #collection = db[collection_name]

    data = {}

    for key in keys:
        cursor = db[collection_name].find({key: {'$exists': True}}, {'time_utc': True, key: True}, sort=[('time_utc', DESCENDING)], limit=nb_of_point)

        data[key] = {'time_utc': [], 'values': []}

        for doc in cursor:
            data[key]['time_utc'].append(doc['time_utc'])
            data[key]['values'].append(doc[key])

    return data


def get_all_last_monitoring(realData=True):
    return get_monitoring(definitions['monitoring'].keys(), 1)


def get_all_last_obs_log():
    return get_data('obs_log', definitions['obs_log'].keys(), 1, dt=None)


def get_all_last_telemetry(realData=True):
    if realData is False:
        return fake_data.fake_telemetry_for_db()
    return get_data('telemetry', definitions['telemetry'].keys(), 1, dt=None)


def get_latest_record(collection_name):
    dt = datetime.now(timezone.utc)
    db = get_db(dt)
    latest_record = list(db[collection_name].find().limit(1).sort([('$natural',-1)]))[0]

    return latest_record

def read_mongo_to_pandas(dt, collection='monitoring', no_id=True):
    """ Read from Mongo and Store into DataFrame """

    # Connect to MongoDB
    if dt is None:
        dt = datetime.now(timezone.utc)
    db = get_db(dt)

    # Make a query to the specific DB and Collection
    #cursor = db[collection].find(query)
    cursor = db[collection].find()


    # Expand the cursor and construct the DataFrame
    df =  pd.DataFrame(list(cursor))

    # Delete the _id
    if no_id:
        del df['_id']

    return df


if __name__ == "__main__":
    print("Converting database definition")
    convert_database_definition()
