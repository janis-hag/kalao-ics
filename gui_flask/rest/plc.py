from flask import Blueprint, request, g

from kalao.plc import laser as k_laser
from kalao.plc import shutter as k_shutter
from kalao.plc import flip_mirror as k_flip_mirror
from kalao.plc import tungsten as k_tungsten
from kalao.plc import calib_unit as k_calib_unit
from kalao.plc import filterwheel as k_filterwheel

from kalao.utils import database as k_database


import json

plc_bp = Blueprint('plc', __name__, url_prefix='/plc')

@plc_bp.route('/status', methods=['GET'])
def plcStatus():

    monitoring = k_database.get_all_last_monitoring()
    filter_position = monitoring["fli_filter_position"]["values"]
    return json.dumps({
        "laser": {
            "status": k_laser.status()
        },
        "shutter": {
            "position": k_shutter.position()
        },
        "flip_mirror": {
            "position": k_flip_mirror.position()
        },
        "tungsten": {
            "status": k_tungsten.status()
        },
        "calib_unit": {
            "status": k_calib_unit.status()
        },
        "filterwheel": {
            "position": filter_position}
        })

@plc_bp.route('/laser/enable', methods=['GET'])
def plcLaserEnable():
    return k_laser.enable();

@plc_bp.route('/laser/disable', methods=['GET'])
def plcLaserDisable():
    return k_laser.disable();

@plc_bp.route('/laser/intensity', methods=['POST'])
def plcLaserIntensity():
    options = request.get_json()
    return str(k_laser.set_intensity(float(options["intensity"])))

@plc_bp.route('/shutter/open', methods=['GET'])
def plcShutterOpen():
    return k_shutter.shutter_open();

@plc_bp.route('/shutter/close', methods=['GET'])
def plcShutterClose():
    return k_shutter.shutter_close();

@plc_bp.route('/flipMirror/up', methods=['GET'])
def plcFlipMirrorUp():
    return k_flip_mirror.up();

@plc_bp.route('/flipMirror/down', methods=['GET'])
def plcFlipMirrorDown():
    return k_flip_mirror.down();

@plc_bp.route('/tungsten/on', methods=['GET'])
def plcTungstenOn():
    return k_tungsten.on();

@plc_bp.route('/tungsten/off', methods=['GET'])
def plcTungstenOff():
    return k_tungsten.off();

@plc_bp.route('/calibUnit/laser', methods=['GET'])
def plcCalibUnitLaser():
    return k_calib_unit.laser_position();

@plc_bp.route('/calibUnit/tungsten', methods=['GET'])
def plcCalibUnitTungsten():
    return k_calib_unit.tungsten_position();

@plc_bp.route('/filterwheel/move', methods=['POST'])
def plcFilterwheelMove():
    options = request.get_json()
    return str(k_filterwheel.set_position(int(options["filter"])))

@plc_bp.route('/calibUnit/move', methods=['POST'])
def plcCalibUnitMove():
    options = request.get_json()
    return str(k_calib_unit.move(float(options["move"])))

@plc_bp.route('/calibUnit/initialise', methods=['GET'])
def plcCalibUnitInitialise():
    return str(k_calib_unit.initialise())
