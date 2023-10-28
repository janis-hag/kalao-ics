'''from flask import Blueprint, request, g

from kalao.cacao import aocontrol as k_aocontrol

import json
import time

system_bp = Blueprint('system', __name__, url_prefix='/modalGain')

@system_bp.route('/status', methods=['GET'])
def systemFStatus():


    try:
        k_aocontrol
        camera_state, camera_substate, camera_start_date = s_system.camera_service("STATUS")
        camera_start_date = camera_start_date.isoformat()
    except:
        camera_state = "Error: Can't read state"
        camera_substate = "Error"
        camera_start_date = "Error"

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
    }),200'''
