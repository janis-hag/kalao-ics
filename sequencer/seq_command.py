#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from kalao.plc import shutter
from kalao.plc import calib_unit
from kalao.plc import flip_mirror
from kalao.plc import laser
from kalao.plc import tungsten
#from kalao.cacao import "..."


PLC_DARK 					= 0x00
PLC_TUNGSTEN_FLAT 			= 0x01
PLC_SKY_FLAT 				= 0x02
PLC_TARGET_OBSERVATION 		= 0x03
PLC_AO_LOOP_CALIBRATION 	= 0x04


def dark():
	tungsten.off()
	shutter.close()

def tungsten_FLAT():
	shutter.close()
	tungsten.on()
	flip_mirror.up()

def sky_FLAT():
	tungsten.off()
	flip_mirror.down()
	shutter.open()


def target_observation():
	tungsten.off()
	shutter.open()
	flip_mirror.down()
	#...

def AO_loop_calibration():
	shutter.close()
	flip_mirror.up()
	laser.set_intensity()
	#"...".start_calib()
	laser.set_intensity(0)


cmd_dict = {
	PLC_DARK: 					dark,
	PLC_TUNGSTEN_FLAT:			tungsten_FLAT,
	PLC_SKY_FLAT: 				sky_FLAT,
	PLC_TARGET_OBSERVATION:		target_observation,
	PLC_AO_LOOP_CALIBRATION: 	AO_loop_calibration
	}
