from kalao.plc import (adc, calib_unit, flip_mirror, laser, shutter,
                       temperature_control, tungsten)
from kalao.plc.core import beckhoff_autoconnect
from kalao.utils import database


def lamps_off():
    """
    Turns the tungsten and laser lamp off.

    :return:
    """

    laser_status = laser.disable()
    tungsten_status = tungsten.off()

    if tungsten_status == 'OFF' and laser_status == 'OFF':
        return 0

    if tungsten_status != 'OFF':
        database.store('obs', {
            'tungsten_log': f'[WARNING] Tungsten lamp did not turn off'
        })

    if laser_status != 'OFF':
        database.store('obs',
                       {'laser_log': f'[WARNING] Laser lamp did not turn off'})

    return 1


@beckhoff_autoconnect
def plc_status(beck=None):
    """
    Query status of all PLC connected devices
    :return: device status dictionary
    """

    # TODO check if all initialised

    temps = temperature_control.get_temperatures(beck=beck)
    cooling_system = temperature_control.get_cooling_status(beck=beck)
    laser_s = laser.plc_status(beck=beck)

    plc_status_values = {
        'shutter_state': shutter.get_state(beck=beck),
        'flip_mirror_position': flip_mirror.get_position(beck=beck),
        'calib_unit_position': calib_unit.plc_status(beck=beck)['lrPosActual'],
        'temp_bench_air': temps['temp_bench_air'],
        'temp_bench_board': temps['temp_bench_board'],
        'temp_water_in': temps['temp_water_in'],
        'temp_water_out': temps['temp_water_out'],
        'laser_state': laser_s['Status'],
        'laser_power': laser_s['Current'],
        'tungsten_state': tungsten.plc_status(beck=beck)['sStatus'],
        'adc1_angle': adc.plc_status(1)['lrPosActual'],
        'adc2_angle': adc.plc_status(2)['lrPosActual'],
        'pump_status': cooling_system['pump_status'],
        'pump_temp': cooling_system['pump_temp'],
        'heater_status': cooling_system['heater_status'],
        'fan_status': cooling_system['fan_status'],
        'flow_value': cooling_system['flow_value']
    }

    return plc_status_values
