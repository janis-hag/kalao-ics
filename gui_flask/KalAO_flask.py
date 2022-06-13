from flask_cors import CORS
from flask import Flask,request,Blueprint,session

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
sys.path.append(path.dirname(path.dirname(path.abspath(path.dirname(__file__)))))

from kalao.cacao import aocontrol as k_aocontrol
from kalao.cacao import telemetry as k_telemetry
from kalao.interface import status as k_status
from kalao.interface import star_centering as k_star_centering
from kalao.utils import database as k_database

def create_app():

    logging.getLogger("waitress").setLevel(logging.ERROR)

    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'kalaoSECRETkeyFORstreams'
    #app.config['SESSION_TYPE'] = 'filesystem'
    #app.secret_key = 'kalaoSECRETkeyFORstreams'
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

        return {
            "monitoring": monitoringMetaData,
            "telemetry": telemetryMetaData,
            "obsLog": obsLogMetaData
        }

    @app.route('/pixelImages', methods=['GET'])
    def pixelImages():

        if 'shm_streams' in app.config:
            shm_streams = app.config['shm_streams']
        else:
            shm_streams = {
                "nuvu_stream" : k_telemetry.create_shm_stream("nuvu_stream"),
                "shwfs_slopes" : k_telemetry.create_shm_stream("shwfs_slopes"),
                "dm01disp" : k_telemetry.create_shm_stream("dm01disp"),
                "shwfs_slopes_flux" : k_telemetry.create_shm_stream("shwfs_slopes_flux"),
                "aol1_mgainfact" : k_telemetry.create_shm_stream("aol1_mgainfact")
            }
            app.config['shm_streams'] = shm_streams

        realData = not bool(request.args.get('random', default = "", type = str))
        stream_list = {}

        stream_list["nuvu_stream"] = k_telemetry.get_stream_data(shm_streams["nuvu_stream"], "nuvu_stream", 0, 2**16-1)
        stream_list["shwfs_slopes"] = k_telemetry.get_stream_data(shm_streams["shwfs_slopes"], "shwfs_slopes", -2, 2)
        stream_list["dm01disp"] = k_telemetry.get_stream_data(shm_streams["dm01disp"], "dm01disp", -1.75, 1.75)
        stream_list["shwfs_slopes_flux"] = k_telemetry.get_stream_data(shm_streams["shwfs_slopes_flux"], "shwfs_slopes_flux", 0, 4*(2**16-1))
        stream_list["aol1_mgainfact"] = k_telemetry.get_stream_data(shm_streams["aol1_mgainfact"], "aol1_mgainfact", 0, 1)

        #return k_telemetry.streams(shm_streams, realData)
        return stream_list

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

    @app.route('/plots/<nb_points>', methods=['GET'])
    def plot(nb_points):
        nb_points = int(nb_points)
        random = bool(request.args.get('random', default = "", type = str))
        if random:
            series = k_status.telemetry_series(random)
        else:
            series = k_database.get_telemetry(['pi_tip', 'pi_tilt'], nb_points)

            for serie_name in series:
                time_arr = []
                for time in series[serie_name]["time_utc"]:
                    time_arr.append(round(datetime.timestamp(time),1))
                series[serie_name]["time"] = time_arr
                series[serie_name].pop("time_utc")

            return series
        obj = {}
        for serie_name in series:
            obj[serie_name] = {"time": [],"values": []}
            nb = 0
            for time in series[serie_name]["time_utc"]:
                if nb < nb_points:
                    obj[serie_name]["time"].append(round(datetime.timestamp(time),1))
                nb+=1
            nb = 0
            for values in series[serie_name]["values"]:
                if nb < nb_points:
                    obj[serie_name]["values"].append(values["values"][0])
                nb+=1

        return obj

    @app.route('/measurements', methods=['GET'])
    def measurements():
        random = bool(request.args.get('random', default = "", type = str))
        return k_status.cacao_measurements(random)

    @app.route('/timeSeries2/<t_start>/<t_end>', methods=['GET'])
    def timeSeries2(t_start,t_end):

        startDay = datetime.fromtimestamp(int(t_start))
        endDay = datetime.fromtimestamp(int(t_end))

        startDay = startDay.astimezone(timezone.utc)
        endDay = endDay.astimezone(timezone.utc)
        print("###",startDay, endDay)
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

    @app.route('/timeSeries/<t_start>/<t_end>', methods=['GET'])
    def timeSeries(t_start,t_end):

        startDay = datetime.fromtimestamp(int(t_start))
        endDay = datetime.fromtimestamp(int(t_end))

        startDay = startDay.astimezone(timezone.utc)
        endDay = endDay.astimezone(timezone.utc)
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

    @app.route('/modalGain', methods=['POST'])
    def modalGain():

        options = request.get_json()
        k_aocontrol.set_modal_gain(options["key"],options["value"])
        print(options)
        print("SET",options["key"],options["value"])
        return "ok"

    return app
