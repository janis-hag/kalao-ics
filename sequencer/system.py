#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : system.py
# @Date : 2021-08-16-13-33
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg

"""
system.py is part of the KalAO Instrument Control Software
(KalAO-ICS). 
"""

from configparser import ConfigParser
from pathlib import Path
import os
import dbus
from datetime import datetime
import time

from kalao.utils import database

# Read config file
parser = ConfigParser()
config_path = os.path.join(Path(os.path.abspath(__file__)).parents[1], 'kalao.config')
parser.read(config_path)


def check_active(unit_name):
    #unit_name = 'kalao_database_updater.service'

    bus, systemd, manager = connect_dbus()

    service = bus.get_object('org.freedesktop.systemd1', object_path = manager.GetUnit(unit_name))

    interface = dbus.Interface(service, dbus_interface='org.freedesktop.DBus.Properties')
    active_state = str(interface.Get('org.freedesktop.systemd1.Unit', 'ActiveState'))

    if active_state == 'active':
        active_entertimestamp = interface.Get('org.freedesktop.systemd1.Unit', 'ActiveEnterTimestamp')
    else:
        active_entertimestamp = interface.Get('org.freedesktop.systemd1.Unit', 'ActiveExitTimestamp')

    active_substate = str(interface.Get('org.freedesktop.systemd1.Unit', 'SubState'))

    # Convert Unix microseconds timestamp into datetime object
    active_entertimestamp = datetime.utcfromtimestamp(int(active_entertimestamp)*10**(-6))

    return active_state, active_substate, active_entertimestamp


def check_enabled(unit_name):
    #unit_name = 'kalao_database_updater.service'

    bus, systemd, manager = connect_dbus()

    enabled_state = manager.GetUnitFileState(unit_name)

    return enabled_state


def unit_control(unit_name, action):
    bus, systemd, manager = connect_dbus()

    action =  action.upper()

    if action == 'RESTART':
        job = manager.RestartUnit(unit_name, 'replace')
    elif action == 'START':
       job = manager.StartUnit(unit_name, 'replace')
    elif action == 'STOP':
       job = manager.StopUnit(unit_name, 'replace')
    elif action == 'STATUS':
        # Status is always returned as long as the action keyword is correct
        pass
    else:
        error_string = ("ERROR: system.unit_control unknown action: "+str(action))
        print(error_string)
        database.store_obs_log({'sequencer_log': error_string})
        return -1

    return check_active(unit_name)

# def restart_unit(unit_name):
#
#     bus, systemd, manager = connect_dbus()
#     #manager.EnableUnitFiles([‘picockpit - client.service’], False, True)
#     #manager.Reload()
#     job = manager.RestartUnit(unit_name, 'replace')
#
#     return job
#
#
# def start_unit(unit_name):
#
#     bus, systemd, manager = connect_dbus()
#     #manager.EnableUnitFiles([‘picockpit - client.service’], False, True)
#     #manager.Reload()
#     job = manager.StartUnit(unit_name, 'replace')
#
#     return job
#
#
# def stop_unit(unit_name):
#
#     bus, systemd, manager = connect_dbus()
#     #manager.EnableUnitFiles([‘picockpit - client.service’], False, True)
#     #manager.Reload()
#     job = manager.StopUnit(unit_name)
#
#     return job


def connect_dbus():
    bus = dbus.SessionBus()
    systemd = bus.get_object('org.freedesktop.systemd1', '/org/freedesktop/systemd1')

    manager = dbus.Interface(systemd, 'org.freedesktop.systemd1.Manager')

    return bus, systemd, manager


def check_status():
    check_kalao_config()
    # TODO verify if anything else needs to be done if check_kalao_config fails

    return_status = {'camera_service': True, 'database_service': True, 'flask_service': True}

    camera_status = camera_service('status')
    if not camera_status[0] == 'active':
        database.store_obs_log({'fli_log': 'WARNING: Camera service down!'})
        return_status['camera_service'] = False

    database_status = database_service('status')
    if not database_status[0] == 'active':
        database.store_obs_log({'database_log': 'WARNING: Database service down!'})
        return_status['database_service'] = False

    flask_status = flask_service('status')
    if not flask_status[0] == 'active':
        database.store_obs_log({'flask_log': 'WARNING: Flask GUI server down!'})
        return_status['flask_service'] = False

    return return_status


def camera_service(action):
    database.store_obs_log({'fli_log': 'Sending '+action+' command to FLI camera server.'})
    unit_name = parser.get('SystemD', 'camera_service')
    status = unit_control(unit_name, action)
    return status


def database_service(action):
    database.store_obs_log({'database_log': 'Sending '+action+' command to database system.'})
    unit_name = parser.get('SystemD', 'database_updater')
    status = unit_control(unit_name, action)
    return status


def flask_service(action):
    database.store_obs_log({'flask_log': 'Sending '+action+' command to flask server.'})
    unit_name = parser.get('SystemD', 'flask_gui')
    status = unit_control(unit_name, action)

    return status


def initialise_services():
    '''
    Initialise all system services and run sanity checks

    :return:
    '''
    ServiceRestartWait = parser.getint('SystemD','ServiceRestartWait')

    flask_service('restart')
    database_service('restart')
    camera_service('restart')

    time.sleep(ServiceRestartWait)

    # Loop as long as not all systems are active.
    if not all(check_status().values()):
        database.store_obs_log({'sequencer_log': 'ERROR: a service is not running! '+str(check_status())})
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return -1

    return 0


def check_kalao_config():

    error = False

    #config_path = os.path.join(Path(os.path.abspath(__file__)).parents[0], 'kalao.config')
    #parser = ConfigParser()
    #parser.read(config_path)

    #PLCSection = parser._sections['PLC']
    PLCSection = dict(parser.items('PLC'))
    FLISection = parser._sections['FLI']
    SEQSection = parser._sections['SEQ']
    GOPSection = parser._sections['GOP']
    FilterWheelSection = parser._sections['FilterWheel']
    FilterPositionSection = parser._sections['FilterPosition']

    # PLC section
    if not PLCSection['ip'].replace('.', '', 3).isdigit():
        print_and_log("Error: wrong values format for PLC 'IP' in kalao.config file")
        error = True
    if not PLCSection['port'].isdigit():
        print_and_log("Error: wrong values format for PLC 'Port' in kalao.config file ")
        error = True
    if not PLCSection['initnbtry'].isdigit():
        print_and_log("Error: wrong values format for PLC 'InitNbTry' in kalao.config file ")
        error = True
    if not PLCSection['inittimeout'].isdigit():
        print_and_log("Error: wrong values format for PLC 'InitTimeout' in kalao.config file ")
        error = True
    if not PLCSection['lasermaxallowed'].replace('.', '', 1).isdigit():
        print_and_log("Error: wrong values format for PLC 'LaserMaxAllowed' in kalao.config file ")
        error = True
    if not PLCSection['laserswitchwait'].isdigit():
        print_and_log("Error: wrong values format for PLC 'LaserSwitchWait' in kalao.config file ")
        error = True
    if not PLCSection['laserposition'].replace('.', '', 1).isdigit():
        print_and_log("Error: wrong values format for PLC 'LaserPosition' in kalao.config file ")
        error = True
    if not PLCSection['tungstenposition'].isdigit():
        print_and_log("Error: wrong values format for PLC 'TungstenPosition' in kalao.config file ")
        error = True
    if not PLCSection['tempbenchairoffset'].isdigit():
        print_and_log("Error: wrong values format for PLC 'TempBenchAirOffset' in kalao.config file ")
        error = True
    if not PLCSection['tempbenchboardoffset'].isdigit():
        print_and_log("Error: wrong values format for PLC 'TempBenchBoardOffset' in kalao.config file ")
        error = True
    if not PLCSection['tempwaterinoffset'].isdigit():
        print_and_log("Error: wrong values format for PLC 'TempWaterInOffset' in kalao.config file ")
        error = True
    if not PLCSection['tempwateroutoffset'].isdigit():
        print_and_log("Error: wrong values format for PLC 'TempWaterOutOffset' in kalao.config file ")
        error = True

    ################
    # FLI section
    ###############
    if not FLISection['exptime'].replace('.', '', 1).isdigit():
        print_and_log("Error: wrong values format for FLI 'ExpTime' in kalao.config file ")
        error = True
    if not FLISection['timesup'].isdigit():
        print_and_log("Error: wrong values format for FLI 'TimeSup' in kalao.config file ")
        error = True
    if not FLISection['ip'].replace('.', '', 3).isdigit():
        print_and_log("Error: wrong values format for FLI 'IP' in kalao.config file ")
        error = True
    if not FLISection['port'].isdigit():
        print_and_log("Error: wrong values format for FLI 'Port' in kalao.config file ")
        error = True

    ###############
    # FilterWheel section
    ###############
    if not FilterWheelSection['enablewait'].isdigit():
        print_and_log("Error: wrong values format for FilterWheel 'EnableWait' in kalao.config file ")
        error = True
    if not FilterWheelSection['initializationwait'].isdigit():
        print_and_log("Error: wrong values format for FilterWheel 'InitializationWait' in kalao.config file ")
        error = True
    if not FilterWheelSection['positionchangewait'].isdigit():
        print_and_log("Error: wrong values format for FilterWheel 'PositionChangeWait' in kalao.config file ")
        error = True

    ################
    # SEQ section
    ###############
    if not SEQSection['ip'].replace('.', '', 3).isdigit():
        print_and_log("Error: wrong values format for SEQ 'IP' in kalao.config file ")
        error = True
    if not SEQSection['port'].isdigit():
        print_and_log("Error: wrong values format for SEQ 'Port' in kalao.config file ")
        error = True

    ################
    # GOP section
    ###############
    if not GOPSection['ip'].replace('.','',3).isdigit():
        print_and_log("Error: wrong values format for GOP 'IP' in kalao.config file ")
        error = True
    if not GOPSection['port'].isdigit():
        print_and_log("Error: wrong values format for GOP 'Port' in kalao.config file ")
        error = True
    if not GOPSection['verbosity'].isdigit():
        print_and_log("Error: wrong values format for GOP 'Verbosity' in kalao.config file ")
        error = True


    if error:
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return -1


def print_and_log(message):
    print(message)
    database.store_obs_log({'sequencer_log': message})
