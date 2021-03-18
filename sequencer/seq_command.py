#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from kalao.plc import shutter
from kalao.plc import calib_unit
from kalao.plc import flip_mirror
from kalao.plc import laser
from kalao.plc import tungsten
from kalao.cacao import control


def dark():
	tungsten.off()
	laser.off()
	shutter.close()
	#Take Image

def tungsten_FLAT():
	shutter.close()
	tungsten.on()
	flip_mirror.up()
	#Select Filter
	#Take Image
	tungsten.off()

def sky_FLAT():
	tungsten.off()
	laser.off()
	flip_mirror.down()
	shutter.open()
	#Select Fitler
	#Take Image

def target_observation():
	tungsten.off()
	laser.off()
	shutter.open()
	flip_mirror.down()
	#Select Filter
	#Centre on target
	control.close_loop()
	#Monitor AO and cancel exposure if needed
	#Take Image
	shutter.close()


def AO_loop_calibration():
	shutter.close()
	flip_mirror.up()
	laser.set_intensity()
	control.start_calib()
	laser.set_intensity(0)
