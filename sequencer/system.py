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
config_path = os.path.join(
        Path(os.path.abspath(__file__)).parents[1], 'kalao.config')
parser.read(config_path)


def _isDigit(x):
    try:
        float(x)
        return True
    except ValueError:
        return False


def check_active(unit_name):
    #unit_name = 'kalao_database_updater.service'

    bus, systemd, manager = connect_dbus()

    service = bus.get_object('org.freedesktop.systemd1',
                             object_path=manager.GetUnit(unit_name))

    interface = dbus.Interface(
            service, dbus_interface='org.freedesktop.DBus.Properties')
    active_state = str(
            interface.Get('org.freedesktop.systemd1.Unit', 'ActiveState'))

    if active_state == 'active':
        active_entertimestamp = interface.Get('org.freedesktop.systemd1.Unit',
                                              'ActiveEnterTimestamp')
    else:
        active_entertimestamp = interface.Get('org.freedesktop.systemd1.Unit',
                                              'ActiveExitTimestamp')

    active_substate = str(
            interface.Get('org.freedesktop.systemd1.Unit', 'SubState'))

    # Convert Unix microseconds timestamp into datetime object
    active_entertimestamp = datetime.utcfromtimestamp(
            int(active_entertimestamp) * 10**(-6))

    bus.close()

    return active_state, active_substate, active_entertimestamp


def check_enabled(unit_name):
    #unit_name = 'kalao_database_updater.service'

    bus, systemd, manager = connect_dbus()

    enabled_state = manager.GetUnitFileState(unit_name)

    bus.close()

    return enabled_state


def unit_control(unit_name, action):
    """
    Function to control systemd unit services.

    :param unit_name: Name of the systemd unit service to control
    :param action: RESTART/START/STOP/STATUS
    :return:
    """
    bus, systemd, manager = connect_dbus()

    action = action.upper()

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
        error_string = ("ERROR: system.unit_control unknown action: " +
                        str(action))
        print(error_string)
        database.store_obs_log({'sequencer_log': error_string})
        return -1

    bus.close()

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
    systemd = bus.get_object('org.freedesktop.systemd1',
                             '/org/freedesktop/systemd1')

    manager = dbus.Interface(systemd, 'org.freedesktop.systemd1.Manager')

    return bus, systemd, manager


def check_status():
    check_kalao_config()
    # TODO verify if anything else needs to be done if check_kalao_config fails

    return_status = {
            'camera_service': True,
            'database_service': True,
            'flask_service': True
    }

    camera_status = camera_service('status')
    if not camera_status[0] == 'active':
        database.store_obs_log({'fli_log': 'WARNING: Camera service down!'})
        return_status['camera_service'] = False

    database_status = database_service('status')
    if not database_status[0] == 'active':
        database.store_obs_log({
                'database_log': 'WARNING: Database service down!'
        })
        return_status['database_service'] = False

    flask_status = flask_service('status')
    if not flask_status[0] == 'active':
        database.store_obs_log({
                'flask_log': 'WARNING: Flask GUI server down!'
        })
        return_status['flask_service'] = False

    return return_status


def camera_service(action):
    """
    Control the camera server systemd service. It accepts one of the four systemctl commands:
    RESTART/START/STOP/STATUS

    :param action: RESTART/START/STOP/STATUS
    :return:
    """

    if not action.upper() == 'STATUS':
        database.store_obs_log({
                'fli_log':
                        'Sending ' + action + ' command to FLI camera server.'
        })
    unit_name = parser.get('SystemD', 'camera_service')
    status = unit_control(unit_name, action)

    return status


def database_service(action):
    """
    Control the database systemd service. It accepts one of the four systemctl commands:
    RESTART/START/STOP/STATUS

    :param action: RESTART/START/STOP/STATUS
    :return:
    """

    if not action.upper() == 'STATUS':
        database.store_obs_log({
                'database_log':
                        'Sending ' + action + ' command to database system.'
        })
    unit_name = parser.get('SystemD', 'database_updater')
    status = unit_control(unit_name, action)

    return status


def flask_service(action):
    """
    Control the flask server systemd service. It accepts one of the four systemctl commands:
    RESTART/START/STOP/STATUS

    :param action: RESTART/START/STOP/STATUS
    :return:
    """

    if not action.upper() == 'STATUS':
        database.store_obs_log({
                'flask_log': 'Sending ' + action + ' command to flask server.'
        })
    unit_name = parser.get('SystemD', 'flask_gui')
    status = unit_control(unit_name, action)

    return status


def gop_service(action):
    if not action.upper() == 'STATUS':
        database.store_obs_log({
                'gop_log': 'Sending ' + action + ' command to gop server.'
        })
    unit_name = parser.get('SystemD', 'gop_server')
    status = unit_control(unit_name, action)

    return status


def watchdog_service(action):
    """
    Control the flask server systemd service. It accepts one of the four systemctl commands:
    RESTART/START/STOP/STATUS

    :param action: RESTART/START/STOP/STATUS
    :return:
    """

    if not action.upper() == 'STATUS':
        database.store_obs_log({
                'flask_log':
                        'Sending ' + action + ' command to safety watchdog.'
        })
    unit_name = parser.get('SystemD', 'safety_watchdog')
    status = unit_control(unit_name, action)

    return status


def initialise_services():
    '''
    Initialise all system services and run sanity checks

    :return:
    '''
    ServiceRestartWait = parser.getint('SystemD', 'ServiceRestartWait')

    database_service('restart')
    camera_service('restart')
    flask_service('restart')
    gop_service('restart')
    watchdog_service('restart')

    time.sleep(ServiceRestartWait)

    # Loop as long as not all systems are active.
    if not all(check_status().values()):
        database.store_obs_log({
                'sequencer_log':
                        'ERROR: a service is not running! ' +
                        str(check_status())
        })
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
    FLISection = dict(parser.items('FLI'))
    SEQSection = dict(parser.items('SEQ'))
    StarfinderSection = dict(parser.items('Starfinder'))
    GOPSection = dict(parser.items('GOP'))
    FilterWheelSection = dict(parser.items('FilterWheel'))
    FilterPositionSection = dict(parser.items('FilterPosition'))

    # PLC section
    if not PLCSection['ip'].replace('.', '', 3).isdigit():
        print_and_log(
                "Error: wrong values format for PLC 'IP' in kalao.config file: "
                + str(PLCSection['ip']))
        error = True
    if not PLCSection['port'].isdigit():
        print_and_log(
                "Error: wrong values format for PLC 'Port' in kalao.config file: "
                + str(PLCSection['port']))
        error = True
    if not PLCSection['initnbtry'].isdigit():
        print_and_log(
                "Error: wrong values format for PLC 'InitNbTry' in kalao.config file: "
                + str(PLCSection['initnbtry']))
        error = True
    if not PLCSection['inittimeout'].isdigit():
        print_and_log(
                "Error: wrong values format for PLC 'InitTimeout' in kalao.config file: "
                + str(PLCSection['inittimeout']))
        error = True
    if not PLCSection['lasermaxallowed'].replace('.', '', 1).isdigit():
        print_and_log(
                "Error: wrong values format for PLC 'LaserMaxAllowed' in kalao.config file: "
                + str(PLCSection['lasermaxallowed']))
        error = True
    if not PLCSection['laserswitchwait'].isdigit():
        print_and_log(
                "Error: wrong values format for PLC 'LaserSwitchWait' in kalao.config file: "
                + str(PLCSection['laserswitchwait']))
        error = True
    if not PLCSection['laserposition'].replace('.', '', 1).isdigit():
        print_and_log(
                "Error: wrong values format for PLC 'LaserPosition' in kalao.config file: "
                + str(PLCSection['laserposition']))
        error = True
    if not PLCSection['tungstenposition'].replace('.', '', 1).isdigit():
        print_and_log(
                "Error: wrong values format for PLC 'TungstenPosition' in kalao.config file: "
                + str(PLCSection['tungstenposition']))
        error = True
    if not PLCSection['tempbenchairoffset'].replace('.', '', 1).replace(
            '-', '', 1).isdigit():
        print_and_log(
                "Error: wrong values format for PLC 'TempBenchAirOffset' in kalao.config file: "
                + str(PLCSection['tempbenchairoffset']))
        error = True
    if not PLCSection['tempbenchboardoffset'].replace('.', '', 1).replace(
            '-', '', 1).isdigit():
        print_and_log(
                "Error: wrong values format for PLC 'TempBenchBoardOffset' in kalao.config file: "
                + str(PLCSection['tempbenchboardoffset']))
        error = True
    if not PLCSection['tempwaterinoffset'].replace('.', '', 1).replace(
            '-', '', 1).isdigit():
        print_and_log(
                "Error: wrong values format for PLC 'TempWaterInOffset' in kalao.config file: "
                + str(PLCSection['tempwaterinoffset']))
        error = True
    if not PLCSection['tempwateroutoffset'].replace('.', '', 1).replace(
            '-', '', 1).isdigit():
        print_and_log(
                "Error: wrong values format for PLC 'TempWaterOutOffset' in kalao.config file: "
                + str(PLCSection['tempwateroutoffset']))
        error = True

    ################
    # FLI section
    ###############
    if not FLISection['exptime'].replace('.', '', 1).isdigit():
        print_and_log(
                "Error: wrong values format for FLI 'ExpTime' in kalao.config file: "
                + str(FLISection['exptime']))
        error = True
    if not FLISection['setuptime'].isdigit():
        print_and_log(
                "Error: wrong values format for FLI 'SetupTime' in kalao.config file: "
                + str(FLISection['setuptime']))
        error = True
    if not FLISection['ip'].replace('.', '', 3).isdigit():
        print_and_log(
                "Error: wrong values format for FLI 'IP' in kalao.config file: "
                + str(FLISection['ip']))
        error = True
    if not FLISection['port'].isdigit():
        print_and_log(
                "Error: wrong values format for FLI 'Port' in kalao.config file: "
                + str(FLISection['port']))
        error = True

    ###############
    # FilterWheel section
    ###############
    if not _isDigit(FilterWheelSection['enablewait']):
        print_and_log(
                "Error: wrong values format for FilterWheel 'EnableWait' in kalao.config file: "
                + str(FilterWheelSection['enablewait']))
        error = True
    if not _isDigit(FilterWheelSection['initializationwait']):
        print_and_log(
                "Error: wrong values format for FilterWheel 'InitializationWait' in kalao.config file: "
                + str(FilterWheelSection['initializationwait']))
        error = True
    if not _isDigit(FilterWheelSection['positionchangewait']):
        print_and_log(
                "Error: wrong values format for FilterWheel 'PositionChangeWait' in kalao.config file: "
                + str(FilterWheelSection['positionchangewait']))
        error = True

    ################
    # SEQ section
    ###############
    if not SEQSection['ip'].replace('.', '', 3).isdigit():
        print_and_log(
                "Error: wrong values format for SEQ 'IP' in kalao.config file: "
                + str(SEQSection['ip']))
        error = True
    if not SEQSection['port'].isdigit():
        print_and_log(
                "Error: wrong values format for SEQ 'Port' in kalao.config file: "
                + str(SEQSection['port']))
        error = True
    if not SEQSection['initduration'].isdigit():
        print_and_log(
                "Error: wrong values format for SEQ 'InitDuration' in kalao.config file: "
                + str(SEQSection['initduration']))
        error = True

    #PointingWaitTime int, PointingTimeOut int

    ################
    # Starfinder section
    ###############
    if not StarfinderSection['centeringtimeout'].isdigit():
        print_and_log(
                "Error: wrong values format for SEQ 'CenteringTimeout' in kalao.config file: "
                + str(SEQSection['centeringtimeout']))
        error = True

    # CenteringTimeout int, FocusingStep float, FocusingPixels int, FocusingDit int, MinFlux int, MaxFlux int, MaxDit int, DitOptimisationTrials int

    ################
    # GOP section
    ###############
    if not (GOPSection['ip'].replace('.', '', 3).isdigit() or
            GOPSection['ip'].isprintable()):
        # IP can be number or hostname
        print_and_log(
                "Error: wrong values format for GOP 'IP' in kalao.config file: "
                + str(GOPSection['ip']))
        error = True
    if not GOPSection['port'].isdigit():
        print_and_log(
                "Error: wrong values format for GOP 'Port' in kalao.config file: "
                + str(GOPSection['port']))
        error = True
    if not GOPSection['verbosity'].isdigit():
        print_and_log(
                "Error: wrong values format for GOP 'Verbosity' in kalao.config file: "
                + str(GOPSection['verbosity']))
        error = True

    if error:
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return -1


def print_and_log(message):
    print(message)
    database.store_obs_log({'sequencer_log': message})
