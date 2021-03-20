#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import threading

from kalao.plc import shutter
from kalao.plc import calib_unit
from kalao.plc import flip_mirror
from kalao.plc import laser
from kalao.plc import tungsten


# Multi-thread fonction: take array of object <function>
# Create a thread for each function and start the function
# Block until the end of each thread
def multi_threading(foncs):
	threads = []

	for fonc in foncs:
		th = threading.Thread(target = fonc)
		th.start()
		threads.append(th)

	for th in threads:
		th.join()


# Define each init process of some composants
# Lunch them in multi-thread
def initialisation():

	def init_FLI_cam():
	pass

	def check_PLC_init_status():
		foncs = [calib_unit.initialise, flip_mirror.initialise, shutter.initialise]
		multi_threading(foncs)

	def init_CACAO():
		pass

	def init_Shutter():
		shutter.initialise()

	init_foncs = [init_FLI_cam, check_PLC_init_status, init_CACAO, init_Shutter]
	multi_threading(init_foncs)
