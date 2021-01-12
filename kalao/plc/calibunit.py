#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : calib_unit
# @Date : 2021-01-02-14-36
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg

"""
calibunit.py is part of the KalAO Instrument Control Software
(KalAO-ICS). 
"""

from . import core
import numbers
from opcua import Client, ua

def move(position=23.36):

    # Connect to OPCUA server
    beck = core.connect()
    # define commands
    motor_nCommand = beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.ctrl.nCommand")
    motor_bExecute = beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.ctrl.bExecute")

    # Set velocity to 1 in case is has been changed
    motor_lrVelocity = beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.ctrl.lrVelocity")
    motor_lrVelocity.set_attribute(ua.AttributeIds.Value,
                                   ua.DataValue(ua.Variant(float(1), motor_lrVelocity.get_data_type_as_variant_type())))
    motor_lrPosition = beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.ctrl.lrPosition")

    # Set reset on error to true in case it has been changed
    motor_bResetError = beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.ctrl.bResetError")
    motor_bResetError.set_attribute(ua.AttributeIds.Value,
                                    ua.DataValue(ua.Variant(True, motor_bResetError.get_data_type_as_variant_type())))

    if isinstance(position, numbers.Number):
        motor_lrPosition.set_attribute(
            ua.AttributeIds.Value, ua.DataValue(ua.Variant(float(position),
                                                           motor_lrPosition.get_data_type_as_variant_type())))
        motor_nCommand.set_attribute(
            ua.AttributeIds.Value, ua.DataValue(ua.Variant(int(3),
                                                           motor_nCommand.get_data_type_as_variant_type())))
        motor_bExecute.set_attribute(ua.AttributeIds.Value,
                                     ua.DataValue(ua.Variant(True, motor_bExecute.get_data_type_as_variant_type())))
        new_position = beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.stat.lrPosActual").get_value()
        # motor_lrPosition = beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.ctrl.lrPosition")
    else:
        print('Expected position to be a number, received: ' + str(position))
        new_position = -99

    # Disconnect from OPCUA server
    beck.disconnect()

    return new_position


def status():
    """
    Query the status of the calibration unit.

    :return: complete status of calibration unit
    """
    # Connect to OPCUA server
    beck = core.connect()

    status_dict = {}

    status_dict['sStatus'] = beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.stat.sStatus").get_value()
    status_dict['sErrorText'] = beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.stat.sErrorText").get_value()
    status_dict['nErrorCode'] = beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.stat.nErrorCode").get_value()
    status_dict['lrVelActual'] = beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.stat.lrVelActual").get_value()
    status_dict['lrVelTarget'] = beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.stat.lrVelTarget").get_value()

    beck.disconnect()

    return status_dict
