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

def check_status():
    check_kalao_config()

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
    FilterPositionSection = parser._sections['FilterPosition']

    if not PLCSection['IP'].replace('.','',3).isdigit():
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
    if not PLCSection['LaserMaxAllowed'].replace('.','',1).isdigit():
        print_and_log("Error: wrong values format for PLC 'LaserMaxAllowed' in kalao.config file ")
        error = True
    if not PLCSection['LaserSwitchWait'].isdigit():
        print_and_log("Error: wrong values format for PLC 'LaserSwitchWait' in kalao.config file ")
        error = True
    if not PLCSection['LaserPosition'].replace('.','',1).isdigit():
        print_and_log("Error: wrong values format for PLC 'LaserPosition' in kalao.config file ")
        error = True
    if not PLCSection['TungstenPosition'].isdigit():
        print_and_log("Error: wrong values format for PLC 'TungstenPosition' in kalao.config file ")
        error = True

    if not FLISection['ExpTime'].replace('.', '', 1).isdigit():
        print_and_log("Error: wrong values format for FLI 'ExpTime' in kalao.config file ")
        error = True
    if not FLISection['TimeSup'].isdigit():
        print_and_log("Error: wrong values format for FLI 'TimeSup' in kalao.config file ")
        error = True
    if not FLISection['IP'].replace('.','',3).isdigit():
        print_and_log("Error: wrong values format for FLI 'IP' in kalao.config file ")
        error = True
    if not FLISection['Port'].isdigit():
        print_and_log("Error: wrong values format for FLI 'Port' in kalao.config file ")
        error = True

    if not SEQSection['IP'].replace('.','',3).isdigit():
        print_and_log("Error: wrong values format for SEQ 'IP' in kalao.config file ")
        error = True
    if not SEQSection['Port'].isdigit():
        print_and_log("Error: wrong values format for SEQ 'Port' in kalao.config file ")
        error = True

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
