#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from os import path
sys.path.append(path.dirname(path.abspath(path.dirname(__file__))))

from kalao.plc import shutter
from kalao.plc import calib_unit
from kalao.plc import flip_mirror
from kalao.plc import laser
from kalao.plc import tungsten
from kalao.fli import control


def dark(dit = 0.05, filepath = None, **kwargs):
	if core.lamps_off() != 0:
		print("Error: failed to turn off lamps")

	if shutter.close() != 'CLOSE':
		print("Error: failed to close the shutter")

	if control.take_image(dit = dit, filepath = filepath) != 0:
		print("Error: failed to store in MondoDB")

def tungsten_FLAT(beck = None, dit = 0.05, filepath = None, **kwargs):
	shutter.close()
	tungsten.on(beck = beck)
	flip_mirror.up()
	#Select Filter
	control.take_image(dit = dit, filepath = filepath)
	tungsten.off(beck = beck)

def sky_FLAT(dit = 0.05, filepath = None, **kwargs):
	core.lamps_off()
	flip_mirror.down()
	shutter.open()
	#Select Fitler
	control.take_image(dit = dit, filepath = filepath)
	shutter.close()

def target_observation(dit = 0.05, filepath = None, **kwargs):
	core.lamps_off()
	shutter.open()
	flip_mirror.down()
	#Select Filter
	#Centre on target
	#cacao.close_loop()
	#Monitor AO and cancel exposure if needed
	control.take_image(dit = dit, filepath = filepath)
	shutter.close()

def AO_loop_calibration(intensity = 0, **kwargs):
	shutter.close()
	flip_mirror.up()
	laser.set_intensity(intensity)
	#cacao.start_calib()
	laser.set_intensity(0)


commandDict = {
	"kal_dark": 				dark,
	"kal_tungsten_FLAT": 		tungsten_FLAT,
	"kal_sky_FLAT": 			sky_FLAT,
	"kal_target_observation":	target_observation,
	"kal_AO_loop_calibration": 	AO_loop_calibration
}
