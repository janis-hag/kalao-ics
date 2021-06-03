from app import app

from flask_cors import CORS
from flask import request

from numpy.random import seed
from numpy.random import randint

import json
import sys
import random
import math

from os import path

#sys.path.append('../includes/kalao-ics')
print("PATH:"+path.dirname(path.dirname(path.abspath(path.dirname(__file__)))))
sys.path.append(path.dirname(path.dirname(path.abspath(path.dirname(__file__)))))

from kalao.cacao import telemetry as k_telemetry
from kalao.interface import status as k_status
from kalao.interface import star_centering as k_star_centering
from kalao.utils import database as k_database

CORS(app)

@app.route('/')
@app.route('/pixelImages', methods=['GET'])
def pixelImages():
    realData = not bool(request.args.get('random', default = "", type = str))
    return k_telemetry.streams(realData)

@app.route('/status', methods=['GET'])
def status():
    realData = not bool(request.args.get('random', default = "", type = str))
    return k_status.latest_obs_log_entry(realData)

@app.route('/monitoring', methods=['GET'])
def monitoring():
    realData = not bool(request.args.get('random', default = "", type = str))
    return k_database.get_all_last_monitoring()

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
    return k_status.cacao_measurements(random)

@app.route('/measurements', methods=['GET'])
def measurements():
    random = bool(request.args.get('random', default = "", type = str))
    return k_status.cacao_measurements(random)

app.run(host="0.0.0.0", port="80");
#app.run(host= '10.194.67.128')
