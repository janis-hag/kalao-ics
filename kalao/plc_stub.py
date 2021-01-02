#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov  9 13:18:31 2020

@author: janis
"""

from opcua import Client, ua
import numbers


def connect(addr="192.168.1.140", port=4840):
    beck = Client("opc.tcp://%s:%d"%(addr, port))
    beck.connect()
    root = beck.get_root_node()
    print(":::::root:::::")
    print(root)
    objects = beck.get_objects_node()
    print(":::::objects:::::")
    print(objects)
    child = objects.get_children()
    print(":::::child:::::")
    print(child)
    print()
    return beck


def browse_recursive(client):
    node = client.get_root_node()
    for childId in node.get_children():
        ch = client.get_node(childId)
        print(ch.get_node_class())
        if ch.get_node_class() == ua.NodeClass.Object:
            browse_recursive(ch)
        elif ch.get_node_class() == ua.NodeClass.Variable:
            try:
                print("{bn} has value {val}".format(
                        bn=ch.get_browse_name(),
                        val=str(ch.get_value())))
            except ua.uaerrors._auto.BadWaitingForInitialData:
                pass


def move_calibration_unit(position=23.36):
    
    # define commands
    motor_nCommand = beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.ctrl.nCommand")
    motor_bExecute = beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.ctrl.bExecute")

    # Set velocity to 1 in case is has been changed
    motor_lrVelocity = beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.ctrl.lrVelocity")
    motor_lrVelocity.set_attribute(ua.AttributeIds.Value, ua.DataValue(ua.Variant(float(1), motor_lrVelocity.get_data_type_as_variant_type())))
    motor_lrPosition = beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.ctrl.lrPosition")

    # Set reset on error to true in case it has been changed
    motor_bResetError = beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.ctrl.bResetError")
    motor_bResetError.set_attribute(ua.AttributeIds.Value, ua.DataValue(ua.Variant(True, motor_bResetError.get_data_type_as_variant_type())))

    if isinstance(position, numbers.Number):
        motor_lrPosition.set_attribute(
                ua.AttributeIds.Value, ua.DataValue(ua.Variant(float(position),
                motor_lrPosition.get_data_type_as_variant_type())))
        motor_nCommand.set_attribute(
                ua.AttributeIds.Value, ua.DataValue(ua.Variant(int(3),
                motor_nCommand.get_data_type_as_variant_type())))
        motor_bExecute.set_attribute(ua.AttributeIds.Value, ua.DataValue(ua.Variant(True, motor_bExecute.get_data_type_as_variant_type())))
        new_position = beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.stat.lrPosActual").get_value()
    else:
        print('Expected position to be a number, received: '+str(position))
        new_position =  -99
        
    return new_position

beck = connect()

browse_recursive(beck)

beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.STATE_IDLE").get_value()

beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.stat.lrPosActual").get_value()

beck.get_node("ns=4; s=MAIN.FlipMirror.stat.lrPosActual").get_value()

beck.get_node("ns=4; s=MAIN.Shutter.stat.lrPosActual").get_value()

#vartype = motor_ncommand.get_data_type_as_variant_type()

motor_nCommand = beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.ctrl.nCommand")
motor_nCommand.set_attribute(ua.AttributeIds.Value, ua.DataValue(ua.Variant(int(1), motor_nCommand.get_data_type_as_variant_type())))

motor_bExecute = beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.ctrl.bExecute")
motor_bExecute.set_attribute(ua.AttributeIds.Value, ua.DataValue(ua.Variant(True, motor_bExecute.get_data_type_as_variant_type())))

motor_lrPosition = beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.ctrl.lrPosition")
motor_lrPosition.set_attribute(ua.AttributeIds.Value, ua.DataValue(ua.Variant(float(23.33), motor_lrPosition.get_data_type_as_variant_type())))

motor_lrVelocity = beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.ctrl.lrVelocity")
motor_lrVelocity.set_attribute(ua.AttributeIds.Value, ua.DataValue(ua.Variant(float(1), motor_lrVelocity.get_data_type_as_variant_type())))

motor_bResetError = beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.ctrl.bResetError")
motor_bResetError.set_attribute(ua.AttributeIds.Value, ua.DataValue(ua.Variant(True, motor_bResetError.get_data_type_as_variant_type())))

beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.stat.sStatus").get_value()
beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.stat.sErrorText").get_value()
beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.stat.nErrorCode").get_value()
beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.stat.lrVelActual").get_value()
beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.stat.lrVelTarget").get_value()


