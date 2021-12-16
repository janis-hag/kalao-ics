#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Nathanaël Restori
"""

import os
from pathlib import Path

from pyMilk.interfacing.isio_shmlib import SHM
from pyMilk.interfacing import isio_shmlib

from CacaoProcessTools import fps, FPS_status

from kalao.utils import database
from kalao.cacao import fake_data, toolbox


def check_stream(stream_name):
	"""
	Function verifies if stream_name exists

	:param stream_name: stream to check existence
	:return: boolean, stream_full_path
	"""
	stream_path = Path(os.environ["MILK_SHM_DIR"])
	stream_name = isio_shmlib._checkSHMName(stream_name)+'.im.shm'
	stream_path = stream_path / stream_name

	if stream_path.exists():
		return True, stream_path
	else:
		return False, stream_path


def check_fps(fps_name):
	"""
	Function verifies if fps_name exists

	:param fps_name: fps to check existence
	:return: boolean, stream_full_path
	"""
	fps_path = Path(os.environ["MILK_SHM_DIR"])
	fps_name = isio_shmlib._checkSHMName(fps_name)+'.fps.shm'
	fps_path = fps_path / fps_name

	if fps_path.exists():
		return True, fps_path
	else:
		return False, fps_path


def _get_stream(name, min, max):

	exists, stream_path = check_stream(name)

	if exists:
		stream = SHM(name)
		# Check turned off to prevent timeout. Data may be obsolete
		data = stream.get_data(check=False)

		return {"data": data.flatten().tolist(), "width": data.shape[1], "height": data.shape[0], "min": min, "max": max}

	else:
		return {"data": 0, "width": 0, "height": 0, "min": 0, "max": 0}


def streams(realData=True):
	if not realData:
		# Returning fake streams for testing purposes
		return fake_data.fake_streams()
	else:
		streams = {}

		streams["nuvu_stream"] = _get_stream("nuvu_stream", 0, 2**16-1)
		streams["shwfs_slopes"] = _get_stream("shwfs_slopes", -2, 2)
		streams["dm01disp"] = _get_stream("dm01disp", -1.75, 1.75)
		streams["shwfs_slopes_flux"] = _get_stream("shwfs_slopes_flux", 0, 4*(2**16-1))
		#streams["aol1_modeval"] = _get_stream("aol1_modeval", -1.75, 1.75) #TODO: uncomment when modal control is working

		return streams


def telemetry_save():
	telemetry = {}

	# NUVU process
	#check if fps exists and is running
	nuvu_exists, nuvu_fps_path = check_fps("nuvu_acquire")

	if nuvu_exists:
		fps_nuvu = fps("nuvu_acquire")

		# Check if it's running
		if fps_nuvu.RUNrunning==1:
			telemetry["nuvu_temp_ccd"]          = fps_nuvu["nuvu_accquire.temp_ccd"]
			telemetry["nuvu_temp_controller"]   = fps_nuvu["nuvu_accquire.temp_controller"]
			telemetry["nuvu_temp_power_supply"] = fps_nuvu["nuvu_accquire.temp_power_supply"]
			telemetry["nuvu_temp_fpga"]         = fps_nuvu["nuvu_accquire.temp_fpga"]
			telemetry["nuvu_temp_heatsink"]     = fps_nuvu["nuvu_accquire.temp_heatsink"]
			telemetry["nuvu_emgain"]            = fps_nuvu["nuvu_accquire.emgain"]
			telemetry["nuvu_exposuretime"]      = fps_nuvu["nuvu_accquire.exposuretime"]

	else:
		pass # Return empty streams

	# SHWFS process
	#check if fps exists and is running
	shwfs_exists, shwfs_fps_path = check_fps("shwfs_process")

	if shwfs_exists:
		fps_slopes = fps("shwfs_process")

		# Check if it's running
		if fps_slopes.RUNrunning==1:
			telemetry["slopes_flux_subaperture"] = fps_slopes["shwfs_process.flux_subaperture"]
			telemetry["slopes_residual"]         = fps_slopes["shwfs_process.residual"]


	# Tip/tilt stream
	#check if fps exists and is running
	tt_exists, tt_fps_path = check_stream("dm02disp")

	if tt_exists:

		tt_stream = SHM("dm02disp")

		# Check turned off to prevent timeout. Data may be obsolete
		tt_data = tt_stream.get_data(check=False)

		telemetry["pi_tip"] = tt_data[0]
		telemetry["pi_tilt"] = tt_data[1]

	database.store_telemetry(telemetry)


def wfs_illumination():
	"""
	Function reads the nuvu stream and return the summed flux in each subaperture

	:return:  subaprtures summed flux
	"""

	# TODO implement masking procdedure in order to only consider usfeul subaps

	stream = SHM("nuvu_acquire")
	frame, subapertures = toolbox.get_roi_and_subapertures(stream.get_data(check=True))

	subapertures_flux = subapertures.sum(axis=(1, 2))

	#TODO reject subaps out of centering zone

	return subapertures_flux