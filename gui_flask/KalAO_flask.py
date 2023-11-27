import json
import logging
import math
import time as time_lib
from datetime import datetime, timezone

import numpy as np

from kalao.cacao import aocontrol as k_aocontrol
from kalao.cacao import toolbox as k_toolbox
from kalao.interfaces import web as k_web
from kalao.plc import filterwheel as k_filterwheel
from kalao.utils import database as k_database
from kalao.utils import starfinder as s_starfinder

from flask import Flask, request
from flask_cors import CORS
from rest.plc import plc_bp
from rest.system import system_bp


def create_app():

    # this line coulde be redundant with     app.logger.setLevel(logging.ERROR)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    #logging.getLogger("werkzeug").setLevel(logging.INFO)

    # Disables logging
    # logging.getLogger('werkzeug').disabled = True

    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'kalaoSECRETkeyFORstreams'
    #app.config['SESSION_TYPE'] = 'filesystem'
    #app.secret_key = 'kalaoSECRETkeyFORstreams'
    app.register_blueprint(plc_bp)
    app.register_blueprint(system_bp)
    #app.logger.setLevel(logging.WARNING)
    app.logger.setLevel(logging.INFO)

    CORS(app)

    @app.route('/metaData', methods=['GET'])
    def metaData():
        def csv_to_json(csvFilePath):
            jsonArray = []

            f = open(csvFilePath, "r")
            for row in f:
                v = list(map(float, row.split(",")))
                v2 = [math.floor(val * 255) for val in v]
                s = {"r": v2[0], "g": v2[1], "b": v2[2]}
                jsonArray.append(s)
            f.close()
            return jsonArray

        colormapsMetaData = {
            "diverging_bwg_20-95_c41_n256":
                csv_to_json('colormaps/diverging_bwg_20-95_c41_n256.csv'),
            "linear_worb_100-25_c53_n256":
                csv_to_json('colormaps/linear_worb_100-25_c53_n256.csv'),
            "glasbey_hv_n256":
                csv_to_json('colormaps/glasbey_hv_n256.csv')
        }

        return {
            "obs": k_database.definitions['obs']['metadata'],
            "monitoring": k_database.definitions['monitoring']['metadata'],
            "telemetry": k_database.definitions['telemetry']['metadata'],
            "filterwheel": k_filterwheel.get_names_to_positions(),
            "colormaps": colormapsMetaData
        }

    @app.route('/pixelImages', methods=['GET'])
    def pixelImages():

        if 'shm_cache' in app.config:
            shm_cache = app.config['shm_cache']
        else:
            shm_cache = {}

            k_toolbox.open_stream_once('nuvu_stream', shm_cache)
            k_toolbox.open_stream_once('shwfs_slopes', shm_cache)
            k_toolbox.open_stream_once('dm01disp', shm_cache)
            k_toolbox.open_stream_once('shwfs_slopes_flux', shm_cache)
            k_toolbox.open_stream_once('aol1_mgainfact', shm_cache)

            app.config['shm_cache'] = shm_cache

        real_data = not bool(request.args.get('random', default="", type=str))

        return k_web.streams(shm_cache, real_data)

    @app.route('/data', methods=['GET'])
    def data():
        real_data = not bool(request.args.get('random', default="", type=str))
        status = k_web.latest_obs_entry(real_data)
        monitoring = k_web.get_all_last_monitoring(real_data)
        telemetry = k_web.get_all_last_telemetry(real_data)
        time = datetime.now(timezone.utc)

        return {
            "time": time,
            "status": status,
            "monitoring": monitoring,
            "telemetry": telemetry
        }, 200

    @app.route('/centeringImage', methods=['POST'])
    def centeringImage():

        if "last_file_date" in request.headers:
            last_file_date = request.headers['last_file_date']
        else:
            last_file_date = None

        options = request.get_json()
        percentile = float(options["percentile"])

        if "x" in options and "y" in options:
            x = options["x"]
            y = options["y"]
        else:
            x = None
            y = None

        real_data = not bool(request.args.get('random', default="", type=str))

        (selection, image,
         file_date) = k_web.get_fli_image(x=x, y=y,
                                          last_file_date=last_file_date,
                                          percentile=percentile,
                                          real_data=real_data)

        if image is None and file_date is None:
            return "Not updated", 204

        imageObject = {
            "data": image.flatten().tolist(),
            "width": image.shape[1],
            "height": image.shape[0],
            "max": np.max(image),
            "min": np.min(image),
            "min_th": 0,
            "max_th": 2**16 - 1,
        }
        jsonObject = json.dumps({
            "selection": selection,
            "image": imageObject,
            "file_date": file_date
        })
        return jsonObject

    @app.route('/plots/<nb_points>', methods=['GET'])
    def plot(nb_points):
        nb_points = int(nb_points)
        real_data = bool(request.args.get('random', default="", type=str))

        series = k_web.tip_tilt(nb_points, real_data)

        for serie_name in series:
            time_arr = []
            for time in series[serie_name]["time_utc"]:
                time_arr.append(round(datetime.timestamp(time), 1))
            series[serie_name]["time"] = time_arr
            series[serie_name].pop("time_utc")

        return series

        obj = {}
        for serie_name in series:
            obj[serie_name] = {"time": [], "values": []}
            nb = 0
            for time in series[serie_name]["time_utc"]:
                if nb < nb_points:
                    obj[serie_name]["time"].append(
                        round(datetime.timestamp(time), 1))
                nb += 1
            nb = 0
            for values in series[serie_name]["values"]:
                if nb < nb_points:
                    obj[serie_name]["values"].append(values["values"][0])
                nb += 1

        return obj

    @app.route('/timeSeries/<t_start>/<t_end>', methods=['GET'])
    def timeSeries(t_start, t_end):

        startDay = datetime.fromtimestamp(int(t_start))
        endDay = datetime.fromtimestamp(int(t_end))

        startDay = startDay.astimezone(timezone.utc)
        endDay = endDay.astimezone(timezone.utc)
        monitoring_data = k_database.read_mongo_to_pandas_by_timestamp(
            'monitoring', startDay, endDay,
            sampling=1500)  #.to_json(orient="split")*/
        telemetry_data = k_database.read_mongo_to_pandas_by_timestamp(
            'telemetry', startDay, endDay,
            sampling=1500)  #.to_json(orient="split")*/
        #data = telemetry_data
        ts = {}
        ts_full = []
        time_list = monitoring_data["time_utc"].tolist()
        if len(time_list) <= 1:
            time_list = []
        time_values = [time_lib.mktime(d.timetuple()) for d in time_list]

        for col in monitoring_data.columns:
            if col != "time_utc":
                values = monitoring_data[col].tolist()
                if len(values) <= 1:
                    values = []

                ts[col] = {"time": [], "values": []}
                for i in range(len(values)):
                    if float(t_start) <= time_values[i] <= float(t_end):
                        ts[col]["time"].append(time_values[i])
                        ts[col]["values"].append(values[i])

        ts_full = []
        time_list = telemetry_data["time_utc"].tolist()
        if len(time_list) <= 1:
            time_list = []
        time_values = [time_lib.mktime(d.timetuple()) for d in time_list]

        for col in telemetry_data.columns:
            if col != "time_utc":
                values = telemetry_data[col].tolist()
                if len(values) <= 1:
                    values = []

                ts[col] = {"time": [], "values": []}
                for i in range(len(values)):
                    if float(t_start) <= time_values[i] <= float(t_end):
                        ts[col]["time"].append(time_values[i])
                        ts[col]["values"].append(values[i])

        return json.dumps(ts)

    @app.route('/modalGain', methods=['POST'])
    def modalGain():

        options = request.get_json()
        k_aocontrol.set_modal_gain(options["key"], options["value"])
        return "ok"

    @app.route('/modalGainFilter', methods=['POST'])
    def modalGainFilter():

        options = request.get_json()
        if "cut_off" in options:
            if "last_mode" in options:
                k_aocontrol.linear_low_pass_modal_gain_filter(
                    options["cut_off"], options["last_mode"])
            else:
                k_aocontrol.linear_low_pass_modal_gain_filter(
                    options["cut_off"])

        return "ok"

    @app.route('/manualCentering', methods=['POST'])
    def manualCentering():

        options = request.get_json()

        x = options["x"]
        y = options["y"]

        s_starfinder.manual_centering(x, y)
        return "ok"

    @app.route('/loop/<type>', methods=['POST'])
    def loop(type):

        options = request.get_json()

        if type == "gain":
            k_aocontrol.set_loopgain(float(options["value"]))
        elif type == "mult":
            k_aocontrol.set_loopmult(float(options["value"]))
        elif type == "limit":
            k_aocontrol.set_looplimit(float(options["value"]))

        return "ok"

    return app


if __name__ == "__main__":

    application = create_app()
    application.run(host='0.0.0.0', port='8080')
