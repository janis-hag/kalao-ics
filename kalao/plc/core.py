#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : beck.py
# @Date : 2021-01-02-14-40
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
beck.py is part of the KalAO Instrument Control Software
(KalAO-ICS).
"""

import time
from functools import wraps

import numpy as np

from opcua import Client, ua

from kalao.definitions.enums import PLCStatus

import config


def connect(addr=config.PLC.ip, port=config.PLC.port):
    beck = Client(f'opc.tcp://{addr}:{port}')
    beck.connect()
    # root = beck.get_root_node()
    # objects = beck.get_objects_node()
    # child = objects.get_children()
    return beck


def beckhoff_autoconnect(fun):
    @wraps(fun)
    def wrapper(*args, beck=None, **kwargs):
        if beck is None:
            disconnect_on_exit = True
            beck = connect()
        else:
            disconnect_on_exit = False

        ret = fun(*args, beck=beck, **kwargs)

        if disconnect_on_exit:
            beck.disconnect()

        return ret

    return wrapper


def motor_send_execute(motor_bExecute):
    motor_bExecute.set_attribute(
        ua.AttributeIds.Value,
        ua.DataValue(
            ua.Variant(True, motor_bExecute.get_data_type_as_variant_type())))


def motor_send_init(motor_nCommand, motor_bExecute):
    motor_nCommand.set_attribute(
        ua.AttributeIds.Value,
        ua.DataValue(
            ua.Variant(int(1),
                       motor_nCommand.get_data_type_as_variant_type())))

    # Execute
    motor_send_execute(motor_bExecute)


@beckhoff_autoconnect
def motor_init(node, force_init=True, beck=None):
    motor_nCommand = beck.get_node(f"{node}.ctrl.nCommand")
    motor_bExecute = beck.get_node(f"{node}.ctrl.bExecute")

    # Check if enabled, if not do enable
    if not beck.get_node(f"{node}.stat.bEnabled").get_value() or force_init:
        motor_bEnable = beck.get_node(f"{node}.ctrl.bEnable")

        motor_bEnable.set_attribute(
            ua.AttributeIds.Value,
            ua.DataValue(
                ua.Variant(True,
                           motor_bEnable.get_data_type_as_variant_type())))

        if not beck.get_node(f"{node}.stat.bEnabled").get_value():
            return -1

    # Check if init, if not do init
    if not beck.get_node(f"{node}.stat.bInitialised").get_value() or force_init:
        motor_send_init(motor_nCommand, motor_bExecute)

        time.sleep(15)
        wait_loop(f'Waiting for {node} initialisation',
                  lambda: motor_is_initialising(node, beck=beck), 5)

        if not beck.get_node(f"{node}.stat.bInitialised").get_value():
            return -1

    return 0


@beckhoff_autoconnect
def motor_move(node, position, velocity, wait, beck=None):
    motor_nCommand = beck.get_node(f"{node}.ctrl.nCommand")
    motor_bExecute = beck.get_node(f"{node}.ctrl.bExecute")

    # Check if initialised
    init_result = motor_init(node, force_init=False, beck=beck)
    if not init_result == 0:
        return init_result

    # Set velocity
    motor_lrVelocity = beck.get_node(f"{node}.ctrl.lrVelocity")

    motor_lrVelocity.set_attribute(
        ua.AttributeIds.Value,
        ua.DataValue(
            ua.Variant(float(velocity),
                       motor_lrVelocity.get_data_type_as_variant_type())))

    # Set target position
    motor_lrPosition = beck.get_node(f"{node}.ctrl.lrPosition")

    motor_lrPosition.set_attribute(
        ua.AttributeIds.Value,
        ua.DataValue(
            ua.Variant(float(position),
                       motor_lrPosition.get_data_type_as_variant_type())))

    # Set move command
    motor_nCommand.set_attribute(
        ua.AttributeIds.Value,
        ua.DataValue(
            ua.Variant(int(3),
                       motor_nCommand.get_data_type_as_variant_type())))

    # Execute
    motor_send_execute(motor_bExecute)

    if wait:
        # Wait for movement
        time.sleep(2)
        wait_loop(f'Waiting for {node} movement',
                  lambda: motor_is_moving(node, beck=beck), 5)

        # Get new position
        return motor_get_position(node, beck=beck)
    else:
        return np.nan


@beckhoff_autoconnect
def motor_get_position(node, beck=None):
    error_code, error_text = get_error(node, beck=beck)

    if error_code != 0:
        return np.nan
    else:
        return beck.get_node(f'{node}.stat.lrPosActual').get_value()


@beckhoff_autoconnect
def motor_is_moving(node, beck=None):
    return beck.get_node(f'{node}.stat.sStatus').get_value().startswith(
        'MOVING')


@beckhoff_autoconnect
def motor_is_initialising(node, beck=None):
    return beck.get_node(f'{node}.stat.sStatus').get_value().startswith(
        'INITIALISING')


@beckhoff_autoconnect
def motor_get_status(node, beck=None):
    enabled = beck.get_node(f'{node}.stat.bEnabled').get_value()
    initialised = beck.get_node(f'{node}.stat.bInitialised').get_value()
    status = beck.get_node(f'{node}.stat.sStatus').get_value()

    if not enabled:
        return PLCStatus.DISABLED
    elif 'INITIALISING' in status:
        return PLCStatus.INITIALISING
    elif not initialised in status:
        return PLCStatus.UNINITIALISED
    elif 'ERROR' in status:
        return PLCStatus.ERROR
    elif 'MOVING' in status:
        return PLCStatus.MOVING
    elif 'STANDING' in status:
        return PLCStatus.STANDING
    else:
        return PLCStatus.UNKNOWN


@beckhoff_autoconnect
def get_error(node, beck=None):
    error_code = beck.get_node(f'{node}.stat.nErrorCode').get_value()

    if error_code != 0:
        error_text = beck.get_node(f'{node}.stat.sErrorText').get_value()

        return error_code, error_text
    else:
        return 0, ''


def wait_loop(message, test, wait_time):
    print(f"{message} ", end='', flush=True)
    while test():
        print(".", end='', flush=True)
        time.sleep(wait_time)
    print(" DONE", flush=True)


@beckhoff_autoconnect
def print_node_tree(node, short=True, beck=None):
    node = beck.get_node(node)

    def print_children(node, prefix):
        children = node.get_children()
        for i, c in enumerate(
                sorted(
                    children, key=lambda c: str(c.get_node_class() != ua.
                                                NodeClass.Variable) + str(c))):
            if i == len(children) - 1:
                prefix_current = prefix + ' └── '
                prefix_next = prefix + '    '
            else:
                prefix_current = prefix + ' ├── '
                prefix_next = prefix + ' │  '

            if c.get_node_class() == ua.NodeClass.Variable:
                value = ' = ' + str(c.get_value())
            else:
                value = ''

            if short:
                node_name = str(c).split('.')[-1]
            else:
                node_name = str(c)

            print(prefix_current + node_name + value)
            print_children(c, prefix_next)

    print(' ' + str(node))
    print_children(node, '')


if __name__ == '__main__':
    print_node_tree('ns=4;s=MAIN')
