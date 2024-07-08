#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : adc.py
# @Date : 2021-08-12-12-00
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
adc.py is part of the KalAO Instrument Control Software
(KalAO-ICS).
"""

import time

import numpy as np
from scipy.optimize import minimize_scalar

from kalao import database, euler, logger
from kalao.cacao import toolbox
from kalao.hardware import filterwheel, plc
from kalao.utils import atmosphere

from opcua import Client

from kalao.definitions.enums import PLCStatus, ReturnCode

import config


class ADCCommand():
    MAX_DISP = 0
    ZERO_DISP = 180


def get_optimal_adc_angle(zenith_angle: float, wavelength: float, T: float,
                          P: float, H: float) -> float:
    target_dispersion = atmosphere.air_dispersion(
        zenith_angle, wavelength, T, P, H) - atmosphere.air_dispersion(
            zenith_angle, config.ADC.dispersion_reference_wavelength, T, P, H)
    dispersion = config.ADC.dispersion[wavelength]

    res = minimize_scalar(lambda x: np.abs(dispersion(x) - target_dispersion),
                          bounds=(0, 180))

    if res.success and res.fun < 1e-2:
        return res.x
    else:
        return 0


def configure(zenith_angle: float | None = None,
              override_threshold: bool = False, blocking: bool = True,
              beck: Client = None) -> int:
    config_fps = toolbox.open_fps_once(config.FPS.CONFIG)

    if config_fps is None or not config_fps.get_param('adc_synchronisation'):
        return 0

    filter_name = filterwheel.get_filter(type=str, from_db=True)

    T = euler.outside_temperature()
    P = euler.outside_pressure()
    H = euler.outside_hygrometry()

    if zenith_angle is None:
        zenith_angle = euler.telescope_zenith_angle()

    wavelength = config.FilterWheel.filter_to_wavelength[filter_name]

    # TODO: in case if filter_name is not in filter_to_wavelength

    if isinstance(wavelength, list):
        angle = 0.

        for w in wavelength:
            angle += get_optimal_adc_angle(zenith_angle, w, T, P, H)

        angle /= len(wavelength)
    elif isinstance(wavelength, float):
        angle = get_optimal_adc_angle(zenith_angle, wavelength, T, P, H)
    else:
        raise Exception(f'Unexpected type {type(wavelength)} for wavelength')

    if override_threshold or np.abs(angle -
                                    get_angle()) > config.ADC.angle_threshold:
        set_angle(angle, blocking=blocking, beck=beck)

    return 0


def set_max_disp(beck: Client = None) -> float:
    return set_angle(ADCCommand.MAX_DISP, beck=beck)


def set_zero_disp(beck: Client = None) -> float:
    return set_angle(ADCCommand.ZERO_DISP, beck=beck)


def set_angle(angle: float, offset: float = 0., blocking: bool = True,
              beck: Client = None) -> float:
    logger.info('adc', f'Setting angle between ADC prisms to {angle}°')

    database.store('obs', {'adc_angle': angle})

    # Motors are face to face, offset by same angle so they are counter-rotating
    rotate(config.PLC.Node.ADC1, config.ADC.max_disp_angle_1 + angle/2 +
           offset, blocking=False, beck=beck)
    rotate(config.PLC.Node.ADC2, config.ADC.max_disp_angle_2 + angle/2 -
           offset, blocking=False, beck=beck)

    if blocking:
        time.sleep(2)

        wait_both(beck=beck)

    # TODO: check motors moved successfully
    return angle


def get_angle() -> float:
    angle = database.get_last_value('obs', 'adc_angle')

    if angle is None:
        return np.inf
    else:
        return angle


def compute_angle_and_offset(angle_adc1: float,
                             angle_adc2: float) -> tuple[float, float]:
    angle1 = angle_adc1 - config.ADC.max_disp_angle_1
    angle2 = angle_adc2 - config.ADC.max_disp_angle_2

    angle = angle1 + angle2
    offset = (angle1-angle2) / 2

    return angle, offset


def rotate(node: str, position: float, velocity: float = config.ADC.velocity,
           blocking: bool = True, beck: Client = None) -> float:
    logger.info('adc',
                f'Moving ADC {node} to position {position}° at {velocity}°/s')

    new_position = plc.motor_move(node, position, velocity, blocking,
                                  beck=beck)

    if blocking:
        logger.info('adc', f'Moved ADC {node} to position {new_position}°')

    return new_position


@plc.autoconnect
def stop(node: str, beck: Client = None) -> None:
    logger.info('adc', f'Stopping ADC {node}')
    plc.motor_send_stop(node, beck=beck)


@plc.autoconnect
def wait(node: str, beck: Client = None) -> int:
    plc.wait_loop(f'Waiting for ADC {node} rotation',
                  lambda: is_moving(node, beck=beck), 5)

    return 0


@plc.autoconnect
def wait_both(beck: Client = None) -> int:
    wait(config.PLC.Node.ADC1, beck=beck)
    wait(config.PLC.Node.ADC2, beck=beck)

    return 0


def get_position(node: str, beck: Client = None) -> float:
    position = plc.motor_get_position(node, beck=beck)

    if np.isnan(position):
        error_code, error_text = plc.get_error(node, beck=beck)
        logger.error('adc', f'{error_text} ({error_code})')

    return position


def is_moving(node: str, beck: Client = None) -> bool:
    return plc.motor_get_status(node, beck=beck) == PLCStatus.MOVING


@plc.autoconnect
def init(node: str, force_init: bool = False,
         beck: Client = None) -> ReturnCode:
    """
    Initialise the ADC motor.
    """
    logger.info('adc', f'Initialising ADC {node}')

    ret_init = plc.motor_init(node, force_init, beck=beck)

    if ret_init != ReturnCode.HW_INIT_SUCCESS:
        logger.error('adc', f'ADC {node} initialisation failed')
    else:
        logger.info('adc', f'ADC {node} initialised')

        if node in config.PLC.initial_state:
            rotate(node, config.PLC.initial_state[node], beck=beck)

    return ret_init


def get_state(node, beck: Client = None) -> PLCStatus:
    return plc.motor_get_status(node, beck=beck)
