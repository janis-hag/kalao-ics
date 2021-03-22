#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from kalao.plc import shutter
from kalao.plc import calib_unit
from kalao.plc import flip_mirror
from kalao.plc import laser
from kalao.plc import tungsten
from kalao.cacao import control


def dark(beckTungsten = None):
	tungsten.off(beckTungsten)
	laser.disable()
	shutter.close()
	#Take Image

def tungsten_FLAT(beckTungsten = None):
	shutter.close()
	tungsten.on(beckTungsten)
	flip_mirror.up()
	#Select Filter
	#Take Image
	tungsten.off(beckTungsten)

def sky_FLAT(beckTungsten = None):
	tungsten.off(beckTungsten)
	laser.disable()
	flip_mirror.down()
	shutter.open()
	#Select Fitler
	#Take Image

def target_observation(beckTungsten = None):
	tungsten.off(beckTungsten)
	laser.disable()
	shutter.open()
	flip_mirror.down()
	#Select Filter
	#Centre on target
	control.close_loop()
	#Monitor AO and cancel exposure if needed
	#Take Image
	shutter.close()

def AO_loop_calibration(intensityLaser = 0.04):
	shutter.close()
	flip_mirror.up()
	laser.set_intensity(intensityLaser)
	control.start_calib()
	laser.set_intensity(0)


commandDict = {
	"kal_dark": 				dark,
	"kal_tungsten_FLAT": 		tungsten_FLAT,
	"kal_sky_FLAT": 			sky_FLAT,
	"kal_target_observation":	target_observation,
	"kal_AO_loop_calibration": 	AO_loop_calibration
}
