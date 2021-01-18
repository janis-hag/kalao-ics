from pymongo import MongoClient
from pymongo import ASCENDING, DESCENDING
from pprint import pprint

from kalao.cacao import fake_data
from kalao.utils import time

from datetime import datetime, timezone

def get_db(datetime):
	client = MongoClient("127.0.0.1")
	return client[time.get_start_of_night(datetime)]

def store_measurements(data):
	now_utc = datetime.now(timezone.utc)

	db = get_db(now_utc)

	data['timestamp'] = now_utc.timestamp()
	data['time_utc'] = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ") # ISO 8601: YYYY-MM-DDThh:mm:ssZ
	data['time_mjd'] = time.get_mjd(now_utc)

	result = db.measurements.insert_one(data)
	pprint(result)

def populate_measurements(data, nb_of_point):
	now_utc = datetime.now(timezone.utc)
	db = get_db(now_utc)

	for key in data.keys():
		cursor = db.measurements.find({key: {'$exists': True}}, {'timestamp': True, key: True}, sort=[('timestamp', DESCENDING)], limit=nb_of_point)

		timestamps = []
		points = []

		for doc in cursor:
			timestamps.append(doc['timestamp'])
			points.append(doc[key])

		data[key] = {'timestamps': timestamps, 'values': points}
