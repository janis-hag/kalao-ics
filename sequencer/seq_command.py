#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from kalao.plc import shutter
from kalao.plc import calib_unit
from kalao.plc import flip_mirror
from kalao.plc import laser
from kalao.plc import tungsten
from kalao.fli import control


def dark(ditControl=0.05, filepathControl=None):
	core.lamps_off()
	shutter.close()
	control.acquire(dit = ditControl, filepath = filepathControl)


def tungsten_FLAT(beckTungsten = None, ditControl=0.05, filepathControl=None):
	shutter.close()
	tungsten.on(beck = beckTungsten)
	flip_mirror.up()
	#Select Filter
	control.acquire(dit = ditControl, filepath = filepathControl)
	tungsten.off(beck = beckTungsten)

def sky_FLAT(ditControl=0.05, filepathControl=None):
	core.lamps_off()
	flip_mirror.down()
	shutter.open()
	#Select Fitler
	control.acquire(dit = ditControl, filepath = filepathControl)
	shutter.close()

def target_observation(ditControl=0.05, filepathControl=None):
	core.lamps_off()
	shutter.open()
	flip_mirror.down()
	#Select Filter
	#Centre on target
	#cacao.close_loop()
	#Monitor AO and cancel exposure if needed
	control.acquire(dit = ditControl, filepath = filepathControl)
	shutter.close()

def AO_loop_calibration(intensityLaser = 0.04):
	shutter.close()
	flip_mirror.up()
	laser.set_intensity(intensity = intensityLaser)
	#cacao.start_calib()
	laser.set_intensity(0)


commandDict = {
	"kal_dark": 				dark,
	"kal_tungsten_FLAT": 		tungsten_FLAT,
	"kal_sky_FLAT": 			sky_FLAT,
	"kal_target_observation":	target_observation,
	"kal_AO_loop_calibration": 	AO_loop_calibration
}
