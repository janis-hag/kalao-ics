from flask import Blueprint, request, g

from sequencer import system as s_system

import json
import time

system_bp = Blueprint('system', __name__, url_prefix='/system')

@system_bp.route('/status', methods=['GET'])
def systemFStatus():

    before = time.process_time()

    try:
        camera_state, camera_substate, camera_start_date = s_system.camera_service("STATUS")
        camera_start_date = camera_start_date.isoformat()
        t1 = (time.process_time()-before)*1000
    except:
        camera_state = "Error: Can't read state"
        camera_substate = "Error"
        camera_start_date = "Error"
        t1 = 999

    before = time.process_time()

    try:
        database_state, database_substate, database_start_date = s_system.database_service("STATUS")
        database_start_date = database_start_date.isoformat()
        t2 = (time.process_time()-before)*1000
    except:
        database_state = "Error: Can't read state"
        database_substate = "Error"
        database_start_date = "Error"
        t2 = 999

    before = time.process_time()

    try:
        flask_state, flask_substate, flask_start_date = s_system.flask_service("STATUS")
        flask_start_date = flask_start_date.isoformat()
        t3 = (time.process_time()-before)*1000
    except:
        flask_state = "Error: Can't read state"
        flask_substate = "Error"
        flask_start_date = "Error"
        t3 = 999

    return json.dumps({
        "camera": {
            "status": {
                "state": camera_state,
                "substate": camera_substate,
                "start_date": camera_start_date,
                "request_time": t1
            }
        },
        "database": {
            "status": {
                "state": database_state,
                "substate": database_substate,
                "start_date": database_start_date,
                "request_time": t2
            }
        },
        "flask": {
            "status": {
                "state": flask_state,
                "substate": flask_substate,
                "start_date": flask_start_date,
                "request_time": t3
            }
        }
    }),200

@system_bp.route('/camera/start', methods=['GET'])
def systemCameraStart():
    s_system.camera_service("RESTART")
    return "", 200

@system_bp.route('/camera/stop', methods=['GET'])
def systemCameraStop():
    s_system.camera_service("STOP")
    return "", 200

@system_bp.route('/database/start', methods=['GET'])
def systemDatabaseStart():
    s_system.database_service("RESTART")
    return "", 200

@system_bp.route('/database/stop', methods=['GET'])
def systemDatabaseStop():
    s_system.database_service("STOP")
    return "", 200

@system_bp.route('/flask/start', methods=['GET'])
def systemFlaskStart():
    s_system.flask_service("RESTART")
    return "", 200
