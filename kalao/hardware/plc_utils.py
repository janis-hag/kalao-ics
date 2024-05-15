from typing import Any

from kalao import logger
from kalao.hardware import (adc, calibunit, cooling, environment, filterwheel,
                            flipmirror, laser, plc, shutter, tungsten)

from opcua import Client

from kalao.definitions.enums import LaserState, ReturnCode, TungstenState

import config


def lamps_off() -> ReturnCode:
    """
    Turns the tungsten and laser lamp off.

    :return:
    """

    laser_status = laser.disable()
    tungsten_status = tungsten.off()

    if tungsten_status == TungstenState.OFF and laser_status == LaserState.OFF:
        return ReturnCode.OK

    if tungsten_status != TungstenState.OFF:
        logger.warn('tungsten', 'Tungsten lamp did not turn off')

    if laser_status != LaserState.OFF:
        logger.warn('laser', 'Laser lamp did not turn off')

    return ReturnCode.GENERIC_ERROR


@plc.autoconnect
def get_all_status(filter_from_db: bool = False,
                   beck: Client = None) -> dict[str, Any]:
    """
    Query status of all PLC connected devices
    :return: device status dictionary
    """

    # TODO check if all initialised

    environment_readings = environment.get_readings(beck=beck)
    cooling_system = cooling.get_status(beck=beck)

    return {
        'shutter_state':
            shutter.get_state(beck=beck),
        'flipmirror_position':
            flipmirror.get_position(beck=beck),
        'calibunit_position':
            calibunit.get_position(beck=beck),
        'calibunit_state':
            calibunit.get_state(beck=beck),
        'laser_state':
            laser.get_state(beck=beck),
        'laser_power':
            laser.get_power(beck=beck),
        'tungsten_state':
            tungsten.get_state(beck=beck),
        'adc1_angle':
            adc.get_position(config.PLC.Node.ADC1, beck=beck),
        'adc1_state':
            adc.get_state(config.PLC.Node.ADC1, beck=beck),
        'adc2_angle':
            adc.get_position(config.PLC.Node.ADC2, beck=beck),
        'adc2_state':
            adc.get_state(config.PLC.Node.ADC2, beck=beck),
        'filterwheel_filter_position':
            filterwheel.get_filter(type=int, from_db=filter_from_db),
        'filterwheel_filter_name':
            filterwheel.get_filter(type=str, from_db=filter_from_db),
        'coolant_temp_in':
            cooling_system['coolant_temp_in'],
        'coolant_temp_out':
            cooling_system['coolant_temp_out'],
        'pump_status':
            cooling_system['pump_status'],
        'pump_temp':
            cooling_system['pump_temp'],
        'heater_status':
            cooling_system['heater_status'],
        'fan_status':
            cooling_system['fan_status'],
        'coolant_flow_rate':
            cooling_system['coolant_flow_rate'],
        'bench_air_temp':
            environment_readings['bench_air_temp'],
        'bench_board_temp':
            environment_readings['bench_board_temp'],
        'bench_air_hygro':
            environment_readings['bench_air_hygro'],
    }
