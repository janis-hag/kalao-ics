#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading

from kalao.plc import shutter
from kalao.plc import calib_unit
from kalao.plc import flip_mirror
from kalao.plc import laser
from kalao.plc import tungsten

def init_FLI_cam():
	pass

def check_PLC_init_status():
	calib_return 		= calib_unit.initialise()
	flip_mirror_return 	= flip_mirror.initialise()
	shutter_return 		= shutter.initialise()
	# print return values for control ?

def init_CACAO():
	pass

def init_Shutter():
	shutter.initialise()

th_FLI = threading.Thread(target = init_FLI_cam)
th_PLC = threading.Thread(target = check_PLC_init_status)
th_CACAO = threading.Thread(target = init_CACAO)
th_Shutter = threading.Thread(target = init_Shutter)

th_FLI.start()
th_PLC.start()
th_CACAO.start()
th_Shutter.start()

th_FLI.join()
th_PLC.join()
th_CACAO.join()
th_Shutter.join()
