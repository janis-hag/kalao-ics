from app import app

from flask_cors import CORS
from flask import request

from numpy.random import seed
from numpy.random import randint

import json
import sys

from os import path
sys.path.append(path.dirname(path.abspath(path.dirname(__file__))))

from kalao.interface import status as k_status

CORS(app)


@app.route('/')
@app.route('/index')
def index():
    return k_status.short()
@app.route('/status', methods=['GET'])
def status():
    return k_status.short()
@app.route('/PLCData', methods=['GET'])
def PLCData():
    return '{"shutter":"OPEN"}'

@app.route('/pixelImages', methods=['GET'])
def pixelImages():
    random = bool(request.args.get('random', default = "", type = str))
    return k_status.cacao_streams(random)

@app.route('/measurements', methods=['GET'])
def measurements():
    random = bool(request.args.get('random', default = "", type = str))
    return k_status.cacao_measurements(random)

@app.route('/plot', methods=['GET'])
def plot():
    random = bool(request.args.get('random', default = "", type = str))
    return k_status.cacao_measurements(random)
app.run(host="0.0.0.0", port="80");
#app.run(host= '10.194.67.128')
