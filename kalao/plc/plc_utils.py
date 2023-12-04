from kalao.plc import (adc, calib_unit, core, flip_mirror, laser, shutter,
                       temperature_control, tungsten)
from kalao.utils import database

from kalao.definitions.enums import LaserState, TungstenState


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
        database.store('obs', {
            'tungsten_log': f'[WARNING] Tungsten lamp did not turn off'
        })

    if laser_status != LaserState.OFF:
        database.store('obs',
                       {'laser_log': f'[WARNING] Laser lamp did not turn off'})

    return -1


@core.beckhoff_autoconnect
def get_all_status(beck=None):
    """
    Query status of all PLC connected devices
    :return: device status dictionary
    """

    # TODO check if all initialised

    temps = temperature_control.get_temperatures(beck=beck)
    cooling_system = temperature_control.get_cooling_status(beck=beck)

    return {
        'shutter_state': shutter.get_state(beck=beck),
        'flip_mirror_position': flip_mirror.get_position(beck=beck),
        'calib_unit_position': calib_unit.get_position(beck=beck),
        'laser_state': laser.get_state(beck=beck),
        'laser_power': laser.get_power(beck=beck),
        'tungsten_state': tungsten.get_state(beck=beck),
        'adc1_angle': adc.get_position(1, beck=beck),
        'adc2_angle': adc.get_position(2, beck=beck),
        'temp_bench_air': temps['temp_bench_air'],
        'temp_bench_board': temps['temp_bench_board'],
        'temp_water_in': temps['temp_water_in'],
        'temp_water_out': temps['temp_water_out'],
        'pump_status': cooling_system['pump_status'],
        'pump_temp': cooling_system['pump_temp'],
        'heater_status': cooling_system['heater_status'],
        'fan_status': cooling_system['fan_status'],
        'flow_value': cooling_system['flow_value']
    }
