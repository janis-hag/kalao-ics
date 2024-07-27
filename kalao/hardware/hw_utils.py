from typing import Any

from opcua import Client

from kalao import logger
from kalao.hardware import (adc, calibunit, cooling, environment, filterwheel,
                            flipmirror, laser, plc, shutter, tungsten)

from kalao.definitions.enums import LaserStatus, ReturnCode, TungstenStatus

import config


def lamps_off() -> ReturnCode:
    """
    Turns the tungsten and laser lamp off.

    :return:
    """

    laser_status = laser.disable()
    tungsten_status = tungsten.off()

    if tungsten_status == TungstenStatus.OFF and laser_status == LaserStatus.OFF:
        return ReturnCode.OK

    if tungsten_status != TungstenStatus.OFF:
        logger.warn('tungsten', 'Tungsten lamp did not turn off')

    if laser_status != LaserStatus.OFF:
        logger.warn('laser', 'Laser lamp did not turn off')

    return ReturnCode.GENERIC_ERROR


@plc.autoconnect
def get_all_status(filter_from_memory: bool = False,
                   beck: Client = None) -> dict[str, Any]:
    """
    Query status of all PLC connected devices
    :return: device status dictionary
    """

    filter_position = filterwheel.get_filter(type=int,
                                             from_memory=filter_from_memory)
    filter_name = filterwheel.translate_to_filter_name(filter_position)

    adc1_angle = adc.get_position(config.PLC.Node.ADC1, beck=beck)
    adc2_angle = adc.get_position(config.PLC.Node.ADC2, beck=beck)

    adc_angle, adc_offset = adc._compute_angle_and_offset(
        adc1_angle, adc2_angle)

    return {
        'shutter_status': shutter.get_status(beck=beck),
        'flipmirror_status': flipmirror.get_status(beck=beck),
        'calibunit_position': calibunit.get_position(beck=beck),
        'calibunit_status': calibunit.get_status(beck=beck),
        'laser_status': laser.get_status(beck=beck),
        'laser_power': laser.get_power(beck=beck),
        'tungsten_status': tungsten.get_status(beck=beck),
        'adc1_angle': adc1_angle,
        'adc1_status': adc.get_status(config.PLC.Node.ADC1, beck=beck),
        'adc2_angle': adc2_angle,
        'adc2_status': adc.get_status(config.PLC.Node.ADC2, beck=beck),
        'adc_angle': adc_angle,
        'adc_offset': adc_offset,
        'filterwheel_filter_position': filter_position,
        'filterwheel_filter_name': filter_name,
    } | cooling.get_all_status(beck=beck) | environment.get_readings(beck=beck)
