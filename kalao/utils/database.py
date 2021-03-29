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


path = os.path.dirname(__file__)
definition_json = path + "/database_definition.json"
definition_yaml = path + "/database_definition.yml"

with open(definition_json) as file:
    definition = json.load(file)

def convert_database_definition():
    with open(definition_yaml, 'r') as yaml_in, open(definition_json, "w") as json_out:
        yaml_object = yaml.safe_load(yaml_in)
        json.dump(yaml_object, json_out)

def get_db(dt):
    client = MongoClient("127.0.0.1")
    return client[kalao_time.get_start_of_night(dt)]

def store_measurements(data):
    now_utc = datetime.now(timezone.utc)
    db = get_db(now_utc)

    data['time_unix'] = now_utc.timestamp()
    data['time_utc'] = kalao_time.get_isotime(now_utc)
    # data['time_utc'] = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ") # ISO 8601: YYYY-MM-DDThh:mm:ssZ
    data['time_mjd'] = kalao_time.get_mjd(now_utc)

    for key in data.keys():
        if not key in definition:
            raise KeyError(f'Inserting unknown key "{key}" in database')

    return db.measurements.insert_one(data)

def get_measurements(keys, nb_of_point, dt=None):
    # If dt is None, get db for today, otherwise get db for the day/night specified  by dt
    if dt is None:
        dt = datetime.now(timezone.utc)
    db = get_db(dt)

    data = {}

    for key in keys:
        cursor = db.measurements.find({key: {'$exists': True}}, {'time_unix': True, key: True}, sort=[('time_unix', DESCENDING)], limit=nb_of_point)

        data[key] = {'timestamps': [], 'values': []}

        for doc in cursor:
            data[key]['timestamps'].append(doc['time_unix'])
            data[key]['values'].append(doc[key])

    return data

def get_all_last_measurements():
    return get_measurements(definition.keys(), 1)

def read_mongo_to_pandas(dt, host='localhost', port=27017, username=None, password=None, no_id=True):
    """ Read from Mongo and Store into DataFrame """

    # Connect to MongoDB
    if dt is None:
        dt = datetime.now(timezone.utc)
    db = get_db(dt)

    # Make a query to the specific DB and Collection
    #cursor = db[collection].find(query)
    cursor = db.find()


    # Expand the cursor and construct the DataFrame
    df =  pd.DataFrame(list(cursor))

    # Delete the _id
    if no_id:
        del df['_id']

    return df

if __name__ == "__main__":
    print("Converting database definition")
    convert_database_definition()
