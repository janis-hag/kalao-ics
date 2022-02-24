#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Nathanaël Restori
"""

import os
from pathlib import Path
import io
import sys

import libtmux

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
	#stream_path = Path(os.environ["MILK_SHM_DIR"])
	stream_path = Path('/tmp/milk')
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
	#fps_path = Path(os.environ["MILK_SHM_DIR"])
	fps_path = Path('/tmp/milk')
	fps_name = isio_shmlib._checkSHMName(fps_name)+'.fps.shm'
	fps_path = fps_path / fps_name

	if fps_path.exists():
		return True, fps_path
	else:
		return False, fps_path


def _get_stream(name, min, max):

	exists, stream_path = check_stream(name)

	if exists:
		stream = SHM(str(stream_path)) #name)
		# Check turned off to prevent timeout. Data may be obsolete
		data = stream.get_data(check=False)

		stream.close()

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
	telemetry_data = {}

	# Create the in-memory "file"
	temp_out = io.StringIO()

	# # NUVU process
	# #check if fps exists and is running
	# nuvu_exists, nuvu_fps_path = check_fps("nuvu_acquire")
	#
	# if nuvu_exists:
	# 	sys.stdout = temp_out
	# 	fps_nuvu = fps("nuvu_acquire")
	# 	sys.stdout = sys.__stdout__
	#
	# 	# Check if it's running
	# 	if fps_nuvu.RUNrunning==1:
	# 		telemetry["nuvu_temp_ccd"]          = fps_nuvu["nuvu_accquire.temp_ccd"]
	# 		telemetry["nuvu_temp_controller"]   = fps_nuvu["nuvu_accquire.temp_controller"]
	# 		telemetry["nuvu_temp_power_supply"] = fps_nuvu["nuvu_accquire.temp_power_supply"]
	# 		telemetry["nuvu_temp_fpga"]         = fps_nuvu["nuvu_accquire.temp_fpga"]
	# 		telemetry["nuvu_temp_heatsink"]     = fps_nuvu["nuvu_accquire.temp_heatsink"]
	# 		telemetry["nuvu_emgain"]            = fps_nuvu["nuvu_accquire.emgain"]
	# 		telemetry["nuvu_exposuretime"]      = fps_nuvu["nuvu_accquire.exposuretime"]
	#
	# else:
	# 	pass # Return empty streams

	# NUVU process
	#check if SHM exists and is running
	nuvu_exists, nuvu_stream_path = check_stream("nuvu_raw")

	server = libtmux.Server()
	try:
		session = server.find_where({ "session_name": "nuvu_ctrl" })
	except:
		session = False

	# If tmux session exists send query temperatures
	if session:
		session.attached_pane.send_keys('\ncam.GetTemperature()')

	if nuvu_exists and session:
		nuvu_stream = SHM("nuvu_raw")

		stream_keywords = nuvu_stream.get_keywords()

		nuvu_stream.close()

		# Check if it's running
		#if fps_nuvu.RUNrunning==1:
		telemetry_data["nuvu_temp_ccd"]          = stream_keywords['T_CCD']
		telemetry_data["nuvu_temp_controller"]   = stream_keywords['T_CNTRLR']
		telemetry_data["nuvu_temp_power_supply"] = stream_keywords['T_PSU']
		telemetry_data["nuvu_temp_fpga"]         = stream_keywords['T_FPGA']
		telemetry_data["nuvu_temp_heatsink"]     = stream_keywords['T_HSINK']
		telemetry_data["nuvu_emgain"]            = stream_keywords['EMGAIN']
		telemetry_data["nuvu_detgain"]            = stream_keywords['DETGAIN']
		telemetry_data["nuvu_exposuretime"]      = stream_keywords['EXPTIME']
		telemetry_data["nuvu_mframerate"] 		= stream_keywords['MFRATE']

	else:
		pass # Return empty streams


	# SHWFS process
	#check if fps exists and is running
	shwfs_exists, shwfs_fps_path = check_fps("shwfs_process")

	pixel_scale =	5.7929690265142/5 # APO-Q-P240-R8,6 FOV per subap / pixels_per_subap

	if shwfs_exists:
		sys.stdout = temp_out
		fps_slopes = fps("shwfs_process")
		sys.stdout = sys.__stdout__

		# Check if it's running
		if fps_slopes.RUNrunning==1:
			telemetry_data["slopes_flux_subaperture"] = fps_slopes.get_param_value_float('flux_subaperture')
			telemetry_data["slopes_residual_pix"]     = fps_slopes.get_param_value_float('residual')
			telemetry_data["slopes_residual_arcsec"]  = fps_slopes.get_param_value_float('residual')*pixel_scale

	# Tip/tilt stream
	#check if fps exists and is running
	tt_exists, tt_fps_path = check_stream("dm02disp")

	if tt_exists:
		tt_stream = SHM("dm02disp")

		# Check turned off to prevent timeout. Data may be obsolete
		tt_data = tt_stream.get_data(check=False)

		tt_stream.close()

		telemetry_data["pi_tip"] = float(tt_data[0])
		telemetry_data["pi_tilt"] = float(tt_data[1])


	database.store_telemetry(telemetry_data)

	temp_out.close()


def wfs_illumination():
	"""
	Function reads the nuvu stream and return the summed flux in each subaperture

	:return:  subaprtures summed flux
	"""

	# TODO implement masking procdedure in order to only consider usfeul subaps

	stream = SHM("nuvu_acquire")
	frame, subapertures = toolbox.get_roi_and_subapertures(stream.get_data(check=True))

	stream.close()

	subapertures_flux = subapertures.sum(axis=(1, 2))

	#TODO reject subaps out of centering zone

	return subapertures_flux


