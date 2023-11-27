import json

from kalao.plc import calib_unit as k_calib_unit
from kalao.plc import filterwheel as k_filterwheel
from kalao.plc import flip_mirror as k_flip_mirror
from kalao.plc import laser as k_laser
from kalao.plc import shutter as k_shutter
from kalao.plc import tungsten as k_tungsten
from kalao.utils import database as k_database

from flask import Blueprint, g, request

plc_bp = Blueprint('plc', __name__, url_prefix='/plc')


@plc_bp.route('/status', methods=['GET'])
def plcStatus():

    return json.dumps({
        "laser": {
            "status": k_laser.plc_status()
        },
        "shutter": {
            "state": k_shutter.get_state()
        },
        "flip_mirror": {
            "position": k_flip_mirror.get_position()
        },
        "tungsten": {
            "status": k_tungsten.plc_status()
        },
        "calib_unit": {
            "status": k_calib_unit.plc_status()
        },
        "filterwheel": {
            "filter": k_filterwheel.get_filter(type=str, from_db=True)
        }
    })


@plc_bp.route('/laser/enable', methods=['GET'])
def plcLaserEnable():
    return k_laser.enable()


@plc_bp.route('/laser/disable', methods=['GET'])
def plcLaserDisable():
    return k_laser.disable()


@plc_bp.route('/laser/intensity', methods=['POST'])
def plcLaserIntensity():
    options = request.get_json()
    return str(k_laser.set_intensity(float(options["intensity"])))


@plc_bp.route('/shutter/open', methods=['GET'])
def plcShutterOpen():
    return k_shutter.open()


@plc_bp.route('/shutter/close', methods=['GET'])
def plcShutterClose():
    return k_shutter.close()


@plc_bp.route('/flipMirror/up', methods=['GET'])
def plcFlipMirrorUp():
    return k_flip_mirror.up()


@plc_bp.route('/flipMirror/down', methods=['GET'])
def plcFlipMirrorDown():
    return k_flip_mirror.down()


@plc_bp.route('/tungsten/on', methods=['GET'])
def plcTungstenOn():
    return k_tungsten.on()


@plc_bp.route('/tungsten/off', methods=['GET'])
def plcTungstenOff():
    return k_tungsten.off()


@plc_bp.route('/calibUnit/laser', methods=['GET'])
def plcCalibUnitLaser():
    return k_calib_unit.move_to_laser_position()


@plc_bp.route('/calibUnit/tungsten', methods=['GET'])
def plcCalibUnitTungsten():
    return k_calib_unit.move_to_tungsten_position()


@plc_bp.route('/filterwheel/move', methods=['POST'])
def plcFilterwheelMove():
    options = request.get_json()
    return str(k_filterwheel.set_filter(int(options["filter"])))


@plc_bp.route('/calibUnit/move', methods=['POST'])
def plcCalibUnitMove():
    options = request.get_json()
    return str(k_calib_unit.move(float(options["move"])))


@plc_bp.route('/calibUnit/initialise', methods=['GET'])
def plcCalibUnitInitialise():
    return str(k_calib_unit.init())
