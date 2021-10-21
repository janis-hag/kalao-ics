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

from kalao.utils import database



def check_active(unit_name):
    #unit_name = 'kalao_database_updater.service'

    bus = dbus.SessionBus()
    systemd = bus.get_object(
        'org.freedesktop.systemd1',
        '/org/freedesktop/systemd1'
    )

    manager = dbus.Interface(
        systemd,
        'org.freedesktop.systemd1.Manager'
    )

    service = bus.get_object('org.freedesktop.systemd1',
         object_path = manager.GetUnit(unit_name))

    interface = dbus.Interface(service,
        dbus_interface='org.freedesktop.DBus.Properties')
    active_state = interface.Get('org.freedesktop.systemd1.Unit', 'ActiveState')
    if str(active_state) == 'active':
        active_entertimestamp = interface.Get('org.freedesktop.systemd1.Unit', 'ActiveEnterTimestamp')
    else:
        active_entertimestamp  = interface.Get('org.freedesktop.systemd1.Unit', 'ActiveExitTimestamp')
    active_substate = interface.Get('org.freedesktop.systemd1.Unit', 'SubState')

    return active_state, active_substate, active_entertimestamp


def check_enabled(unit_name):
    #unit_name = 'kalao_database_updater.service'

    bus = dbus.SessionBus()
    systemd = bus.get_object(
        'org.freedesktop.systemd1',
        '/org/freedesktop/systemd1'
    )

    manager = dbus.Interface(
        systemd,
        'org.freedesktop.systemd1.Manager'
    )

    enabled_state = manager.GetUnitFileState(unit_name)

    return enabled_state


def restart_unit(unit_name):

    bus = dbus.SessionBus()
    systemd = bus.get_object(
        'org.freedesktop.systemd1',
        '/org/freedesktop/systemd1'
    )

    manager = dbus.Interface(
        systemd,
        'org.freedesktop.systemd1.Manager'
    )

    #manager.EnableUnitFiles([‘picockpit - client.service’], False, True)
    #manager.Reload()
    job = manager.RestartUnit(unit_name, 'replace')

    return job


def check_status():
    check_kalao_config()
    # TODO camera service check
    # TODO database service check


def camera_service():
    # TODO status, stop, start
    pass


def database_service():
    # TODO status, stop, start
    pass


def check_kalao_config():

    error = False

    config_path = os.path.join(Path(os.path.abspath(__file__)).parents[1], 'kalao.config')
    parser = ConfigParser()
    parser.read(config_path)

    PLCSection = parser._sections['PLC']
    FLISection = parser._sections['FLI']
    SEQSection = parser._sections['SEQ']
    GOPSection = parser._sections['GOP']
    FilterWheelSection = parser._sections['FilterWheel']
    FilterPositionSection = parser._sections['FilterPosition']

    # PLC section
    if not PLCSection['IP'].replace('.', '', 3).isdigit():
        print_and_log("Error: wrong values format for PLC 'IP' in kalao.config file")
        error = True
    if not PLCSection['Port'].isdigit():
        print_and_log("Error: wrong values format for PLC 'Port' in kalao.config file ")
        error = True
    if not PLCSection['InitNbTry'].isdigit():
        print_and_log("Error: wrong values format for PLC 'InitNbTry' in kalao.config file ")
        error = True
    if not PLCSection['InitTimeout'].isdigit():
        print_and_log("Error: wrong values format for PLC 'InitTimeout' in kalao.config file ")
        error = True
    if not PLCSection['LaserMaxAllowed'].replace('.', '', 1).isdigit():
        print_and_log("Error: wrong values format for PLC 'LaserMaxAllowed' in kalao.config file ")
        error = True
    if not PLCSection['LaserSwitchWait'].isdigit():
        print_and_log("Error: wrong values format for PLC 'LaserSwitchWait' in kalao.config file ")
        error = True
    if not PLCSection['LaserPosition'].replace('.', '', 1).isdigit():
        print_and_log("Error: wrong values format for PLC 'LaserPosition' in kalao.config file ")
        error = True
    if not PLCSection['TungstenPosition'].isdigit():
        print_and_log("Error: wrong values format for PLC 'TungstenPosition' in kalao.config file ")
        error = True
    if not PLCSection['TempBenchAirOffset'].isdigit():
        print_and_log("Error: wrong values format for PLC 'TempBenchAirOffset' in kalao.config file ")
        error = True
    if not PLCSection['TempBenchBoardOffset'].isdigit():
        print_and_log("Error: wrong values format for PLC 'TempBenchBoardOffset' in kalao.config file ")
        error = True
    if not PLCSection['TempWaterInOffset'].isdigit():
        print_and_log("Error: wrong values format for PLC 'TempWaterInOffset' in kalao.config file ")
        error = True
    if not PLCSection['TempWaterOutOffset'].isdigit():
        print_and_log("Error: wrong values format for PLC 'TempWaterOutOffset' in kalao.config file ")
        error = True

    ################
    # FLI section
    ###############
    if not FLISection['ExpTime'].replace('.', '', 1).isdigit():
        print_and_log("Error: wrong values format for FLI 'ExpTime' in kalao.config file ")
        error = True
    if not FLISection['TimeSup'].isdigit():
        print_and_log("Error: wrong values format for FLI 'TimeSup' in kalao.config file ")
        error = True
    if not FLISection['IP'].replace('.', '', 3).isdigit():
        print_and_log("Error: wrong values format for FLI 'IP' in kalao.config file ")
        error = True
    if not FLISection['Port'].isdigit():
        print_and_log("Error: wrong values format for FLI 'Port' in kalao.config file ")
        error = True

    ###############
    # FilterWheel section
    ###############
    if not FilterWheelSection['EnableWait'].isdigit():
        print_and_log("Error: wrong values format for FilterWheel 'EnableWait' in kalao.config file ")
        error = True
    if not FilterWheelSection['InitializationWait'].isdigit():
        print_and_log("Error: wrong values format for FilterWheel 'InitializationWait' in kalao.config file ")
        error = True
    if not FilterWheelSection['PositionChangeWait'].isdigit():
        print_and_log("Error: wrong values format for FilterWheel 'PositionChangeWait' in kalao.config file ")
        error = True

    ################
    # SEQ section
    ###############
    if not SEQSection['IP'].replace('.', '', 3).isdigit():
        print_and_log("Error: wrong values format for SEQ 'IP' in kalao.config file ")
        error = True
    if not SEQSection['Port'].isdigit():
        print_and_log("Error: wrong values format for SEQ 'Port' in kalao.config file ")
        error = True

    ################
    # GOP section
    ###############
    if not GOPSection['IP'].replace('.','',3).isdigit():
        print_and_log("Error: wrong values format for GOP 'IP' in kalao.config file ")
        error = True
    if not GOPSection['Port'].isdigit():
        print_and_log("Error: wrong values format for GOP 'Port' in kalao.config file ")
        error = True
    if not GOPSection['Verbosity'].isdigit():
        print_and_log("Error: wrong values format for GOP 'Verbosity' in kalao.config file ")
        error = True


    if error:
        database.store_obs_log({'sequencer_status': 'ERROR'})
        return -1


def print_and_log(message):
    print(message)
    database.store_obs_log({'sequencer_log': message})
