from kalao import logger
from kalao.plc import (adc, calibunit, core, filterwheel, flipmirror, laser,
                       shutter, temperature_control, tungsten)

from kalao.definitions.enums import LaserState, TungstenState

import config


def lamps_off():
    """
    Turns the tungsten and laser lamp off.

    :return:
    """

    laser_status = laser.disable()
    tungsten_status = tungsten.off()

    if tungsten_status == TungstenState.OFF and laser_status == LaserState.OFF:
        return 0

    if tungsten_status != TungstenState.OFF:
        logger.warn('tungsten', 'Tungsten lamp did not turn off')

    if laser_status != LaserState.OFF:
        logger.warn('laser', 'Laser lamp did not turn off')

    return -1


@core.beckhoff_autoconnect
def get_all_status(beck=None, filter_from_db=False):
    """
    Query status of all PLC connected devices
    :return: device status dictionary
    """

    # TODO check if all initialised

    temps = temperature_control.get_temperatures(beck=beck)
    cooling_system = temperature_control.get_cooling_status(beck=beck)

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
        'temp_bench_air':
            temps['temp_bench_air'],
        'temp_bench_board':
            temps['temp_bench_board'],
        'temp_water_in':
            temps['temp_water_in'],
        'temp_water_out':
            temps['temp_water_out'],
        'hygro_bench_air':
            temps['hygro_bench_air'],
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
    }
