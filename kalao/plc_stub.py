#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : test2
# @Date : 2020-11-09-13-18
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg

"""
plc.py is part of the KalAO Instrument Control Software
(KalAO-ICS).
"""



beck = connect()

browse_recursive(beck)

beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.STATE_IDLE").get_value()

beck.get_node("ns=4; s=MAIN.Linear_Standa_8MT.stat.lrPosActual").get_value()



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



