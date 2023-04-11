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

from . import core
import numbers
from opcua import ua
from time import sleep
from configparser import ConfigParser
from pathlib import Path
import os

config_path = os.path.join(
        Path(os.path.abspath(__file__)).parents[2], 'kalao.config')
# Read config file
parser = ConfigParser()
parser.read(config_path)

adc_name = {1: 'ADC1_Newport_PR50PP.motor', 2: 'ADC2_Newport_PR50PP.motor'}


def rotate(adc_id, position=0, beck=None):
    # Connect to OPCUA server
    beck, disconnect_on_exit = core.check_beck(beck)

    # define commands
    motor_nCommand = beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] +
                                   ".ctrl.nCommand")
    motor_bExecute = beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] +
                                   ".ctrl.bExecute")

    # Check if initialised
    init_result = initialise(adc_id, force_init=False, beck=beck,
                             motor_nCommand=motor_nCommand,
                             motor_bExecute=motor_bExecute)
    if not init_result == 0:
        return init_result

    # Set velocity to 1 in case is has been changed
    motor_lrVelocity = beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] +
                                     ".ctrl.lrVelocity")
    motor_lrVelocity.set_attribute(
            ua.AttributeIds.Value,
            ua.DataValue(
                    ua.Variant(
                            float(1),
                            motor_lrVelocity.get_data_type_as_variant_type())))
    motor_lrPosition = beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] +
                                     ".ctrl.lrPosition")

    if isinstance(position, numbers.Number):
        # Set target position
        motor_lrPosition.set_attribute(
                ua.AttributeIds.Value,
                ua.DataValue(
                        ua.Variant(
                                float(position),
                                motor_lrPosition.get_data_type_as_variant_type(
                                ))))
        # Set move command
        motor_nCommand.set_attribute(
                ua.AttributeIds.Value,
                ua.DataValue(
                        ua.Variant(
                                int(3),
                                motor_nCommand.get_data_type_as_variant_type())
                ))
        # Execute
        send_execute(motor_bExecute)
        while beck.get_node(
                "ns=4; s=MAIN." + adc_name[adc_id] +
                ".stat.sStatus").get_value() == 'MOVING in Positioning Mode':
            print('.')
            sleep(5)
        # Get new position
        new_position = beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] +
                                     ".stat.lrPosActual").get_value()
        # motor_lrPosition = beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] + ".ctrl.lrPosition")
    else:
        print('Expected position to be a number, received: ' + str(position))
        new_position = -1

    if disconnect_on_exit:
        beck.disconnect()

    return new_position


def status(adc_id, beck=None):
    """
    Query the status of the ADC motor.

    :return: complete status of calibration unit
    """
    # Connect to OPCUA server
    beck, disconnect_on_exit = core.check_beck(beck)

    status_dict = core.device_status(adc_name[adc_id], beck=beck)
    # status_dict = {'sStatus': beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] + ".stat.sStatus").get_value(),
    #                'sErrorText': beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] + ".stat.sErrorText").get_value(),
    #                'nErrorCode': beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] + ".stat.nErrorCode").get_value(),
    #                'lrVelActual': beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] + ".stat.lrVelActual").get_value(),
    #                'lrVelTarget': beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] + ".stat.lrVelTarget").get_value(),
    #                'lrPosActual': beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] + ".stat.lrPosActual").get_value(),
    #                'lrPosition': beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] + ".ctrl.lrPosition").get_value()}

    if disconnect_on_exit:
        beck.disconnect()

    return status_dict


def check_error(adc_id, beck=None):
    # Connect to OPCUA server
    beck, disconnect_on_exit = core.check_beck(beck)

    if beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] +
                     ".stat.sErrorText").get_value() == 0:
        adc_status = 0
    else:
        adc_status = 'ERROR'

    if disconnect_on_exit:
        beck.disconnect()

    return adc_status


def initialise(adc_id, force_init=False, beck=None, motor_nCommand=None,
               motor_bExecute=None):
    """
    Initialise the ADC motor.

    :param motor_bExecute:
    :param adc_id:
    :param force_init:
    :param beck: the handle for the plc connection
    :param motor_nCommand: handle to send commands to the motor
    :return: returns 0 on success and error code on failure
    """
    # Connect to OPCUA server
    beck, disconnect_on_exit = core.check_beck(beck)

    init_status = 0

    if motor_nCommand is None:
        # define commands
        motor_nCommand = beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] +
                                       ".ctrl.nCommand")

    if motor_bExecute is None:
        motor_bExecute = beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] +
                                       ".ctrl.bExecute")

    # Check if enabled, if no do enable
    if not beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] +
                         ".stat.bEnabled").get_value() or force_init:
        motor_bEnable = beck.get_node("ns = 4; s = MAIN." + adc_name[adc_id] +
                                      ".ctrl.bEnable")
        motor_bEnable.set_attribute(
                ua.AttributeIds.Value,
                ua.DataValue(
                        ua.Variant(
                                True,
                                motor_bEnable.get_data_type_as_variant_type()))
        )
        if not beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] +
                             ".stat.bEnabled").get_value():
            error = 'ERROR: ' + str(
                    beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] +
                                  ".stat.nErrorCode").get_value())
            init_status = error

    # Check if init, if not do init
    if not beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] +
                         ".stat.bInitialised").get_value() or force_init:
        send_init(motor_nCommand, motor_bExecute)
        print('Initalising ADC motor' + str(adc_id))
        sleep(15)
        while beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] +
                            ".stat.sStatus").get_value() == 'INITIALISING':
            print('.')
            sleep(15)
        if not beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] +
                             ".stat.bInitialised").get_value():
            error = 'ERROR: ' + str(
                    beck.get_node("ns=4; s=MAIN." + adc_name[adc_id] +
                                  ".stat.nErrorCode").get_value())
            init_status = error

    if disconnect_on_exit:
        beck.disconnect()

    return init_status


def send_execute(motor_bExecute):

    motor_bExecute.set_attribute(
            ua.AttributeIds.Value,
            ua.DataValue(
                    ua.Variant(
                            True,
                            motor_bExecute.get_data_type_as_variant_type())))


def send_init(motor_nCommand, motor_bExecute):
    motor_nCommand.set_attribute(
            ua.AttributeIds.Value,
            ua.DataValue(
                    ua.Variant(
                            int(1),
                            motor_nCommand.get_data_type_as_variant_type())))
    # Execute
    send_execute(motor_bExecute)
