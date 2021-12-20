from flask_cors import CORS
from flask import Flask,request,Blueprint

from rest.plc import plc_bp
from rest.system import system_bp
from datetime import datetime, timedelta, timezone
import pytz


from numpy.random import seed
from numpy.random import randint

import json
import sys
import random
import math
import yaml
import time as time_lib

import logging

from os import path

#sys.path.append('../includes/kalao-ics')
print("PATH:"+path.dirname(path.dirname(path.abspath(path.dirname(__file__)))))
sys.path.append(path.dirname(path.dirname(path.abspath(path.dirname(__file__)))))

from kalao.cacao import telemetry as k_telemetry
from kalao.interface import status as k_status
from kalao.interface import star_centering as k_star_centering
from kalao.utils import database as k_database

def create_app():

    logging.getLogger("waitress").setLevel(logging.ERROR)

    app = Flask(__name__)

    app.register_blueprint(plc_bp)
    app.register_blueprint(system_bp)

    CORS(app)

    @app.route('/metaData', methods=['GET'])
    def metaData():
        projectPath = path.dirname(path.dirname(path.abspath(path.dirname(__file__))))

        monitoringMetaData = {}
        obsLogMetaData = {}
        telemetryMetaData = {}

        # Read parameters.yml
        file_path = projectPath+'/kalao-ics/kalao/utils/database_definition_monitoring.yml'
        with open(file_path, 'r') as param:
            try:
                monitoringMetaData = yaml.safe_load(param)
            except yaml.YAMLError as exc:
                print("Error while trying to load parametersfrom "+file_path+" file")

        file_path = projectPath+'/kalao-ics/kalao/utils/database_definition_obs_log.yml'
        with open(file_path, 'r') as param:
            try:
                obsLogMetaData = yaml.safe_load(param)
            except yaml.YAMLError as exc:
                print("Error while trying to load parametersfrom "+file_path+" file")

        file_path = projectPath+'/kalao-ics/kalao/utils/database_definition_telemetry.yml'
        with open(file_path, 'r') as param:
            try:
                telemetryMetaData = yaml.safe_load(param)
            except yaml.YAMLError as exc:
                print("Error while trying to load parametersfrom "+file_path+" file")

        '''
        json_file = open(projectPath+"/kalao-ics/kalao/utils/database_definition_monitoring.json")
        monitoringMetaData = json.load(json_file)
        json_file.close()

        json_file = open(projectPath+"/kalao-ics/kalao/utils/database_definition_obs_log.json")
        obsLogMetaData = json.load(json_file)
        json_file.close()

        json_file = open(projectPath+"/kalao-ics/kalao/utils/database_definition_telemetry.json")
        telemetryMetaData = json.load(json_file)
        json_file.close()
        '''

        return {
            "monitoring": monitoringMetaData,
            "telemetry": telemetryMetaData,
            "obsLog": obsLogMetaData
        }

    @app.route('/pixelImages', methods=['GET'])
    def pixelImages():
        realData = not bool(request.args.get('random', default = "", type = str))
        return k_telemetry.streams(realData)

    @app.route('/data', methods=['GET'])
    def data():
        realData = not bool(request.args.get('random', default = "", type = str))
        status = k_status.latest_obs_log_entry(realData)
        monitoring = k_database.get_all_last_monitoring()
        telemetry = k_database.get_all_last_telemetry(realData)
        time = datetime.now(timezone.utc)

        return {
            "time": time,
            "status": status,
            "monitoring": monitoring,
            "telemetry": telemetry
        }, 200

    @app.route('/centeringImage', methods=['GET'])
    def centeringImage():
        realData = not bool(request.args.get('random', default = "", type = str))
        binFactor = not bool(request.args.get('binFactor', default = "", type = str))
        x = not bool(request.args.get('x', default = "", type = str))
        y = not bool(request.args.get('y', default = "", type = str))
        (selection,image) = k_star_centering.fli_view(binFactor,x,y,realData)
        #if realData:
        #    lat_list = [item for sublist in image for item in sublist]
        #else:
        #    image = [random.choices(range(1,100), k=1024) for _ in range(1024)]

        #flat_list = [item for sublist in image for item in sublist]
        flat_list = image.flatten().tolist()
        imageObject = {
            "data": flat_list,
            "height": math.sqrt(len(flat_list)),
            "max": max(flat_list),
            "min": min(flat_list),
            "width": math.sqrt(len(flat_list))
        }
        jsonObject = json.dumps({"selection": selection, "image": imageObject})
        return jsonObject;

    @app.route('/plots', methods=['GET'])
    def plot():
        random = bool(request.args.get('random', default = "", type = str))
        series = k_status.telemetry_series(random)
        limit = 100
        obj = {}
        for serie_name in series:
            obj[serie_name] = {"time": [],"values": []}
            nb = 0
            for time in series[serie_name]["time_utc"]:
                if nb < limit:
                    obj[serie_name]["time"].append(round(datetime.timestamp(time),1))
                nb+=1
            nb = 0
            for values in series[serie_name]["values"]:
                if nb < limit:
                    obj[serie_name]["values"].append(values["values"][0])
                nb+=1

        return obj

    @app.route('/measurements', methods=['GET'])
    def measurements():
        random = bool(request.args.get('random', default = "", type = str))
        return k_status.cacao_measurements(random)

    @app.route('/timeSeries/<t_start>/<t_end>', methods=['GET'])
    def timeSeries(t_start,t_end):
        #print(t_start,t_end)
        #def read_mongo_to_pandas(dt, days=1, collection='monitoring', no_id=True):

        startDay = datetime.fromtimestamp(int(t_start))
        endDay = datetime.fromtimestamp(int(t_end))
        #startDay = datetime.fromisoformat(t_start)
        #endDay = datetime.fromisoformat(t_end)
        startDay = startDay.astimezone(timezone.utc)
        endDay = endDay.astimezone(timezone.utc)
        #startDay = current_tz.localize(datetime.strptime(t_start, '%a, %d %b %Y %H:%M:%S'))
        #endDay = current_tz.localize(datetime.strptime(t_end, '%a, %d %b %Y %H:%M:%S'))
        #startDay = datetime.fromtimestamp(int(t_start))
        #endDay = datetime.fromtimestamp(int(t_end))
        data = k_database.read_mongo_to_pandas_by_timestamp(startDay, endDay) #.to_json(orient="split")*/
        ts = {}
        ts_full = []
        time_list = data["time_utc"].tolist()
        if len(time_list) <= 1:
            time_list = []
        time_values = [time_lib.mktime(d.timetuple()) for d in time_list]

        for col in data.columns:
            if col != "time_utc":
                values = data[col].tolist()
                if len(values) <= 1:
                    values = []

                ts[col] = {
                    "time": [],
                    "values": []
                }
                for i in range(len(values)):
                    if time_values[i] >= float(t_start) and time_values[i] <= float(t_end) :
                        ts[col]["time"].append(time_values[i])
                        ts[col]["values"].append(values[i])

        return json.dumps(ts);
        #print(data)
        '''
        random = bool(request.args.get('random', default = "", type = str))
        series = k_status.telemetry_series(random)
        limit = 100
        obj = {}
        for serie_name in series:
            obj[serie_name] = {"time": [],"values": []}
            nb = 0
            for time in series[serie_name]["time_utc"]:
                if nb < limit:
                    obj[serie_name]["time"].append(round(datetime.timestamp(time),1))
                nb+=1
            nb = 0
            for values in series[serie_name]["values"]:
                if nb < limit:
                    obj[serie_name]["values"].append(values["values"][0])
                nb+=1

        return obj,200'''

        #return data,200

    return app
