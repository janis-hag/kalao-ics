#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Nathanaël Restori
"""

from pathlib import Path
import numpy as np

import libtmux

from pyMilk.interfacing.isio_shmlib import SHM
from pyMilk.interfacing import isio_shmlib

from CacaoProcessTools import fps, FPS_status

from kalao.utils import database
from kalao.cacao import fake_data


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


def create_shm_stream(name):

	exists, stream_path = check_stream(name)

	if exists:
		return SHM(str(stream_path))
	else:
		return None


def _get_stream(name, min_value, max_value):
	"""
	Opens an existing stream after having verified it's existence.

	:param name:
	:param min_value:
	:param max_value:
	:return:
	"""
	exists, stream_path = check_stream(name)

	if exists:
		shm_stream = SHM(str(stream_path)) #name)
		#shm_stream = SHM(name) #name)
		# Check turned off to prevent timeout. Data may be obsolete
		data = shm_stream.get_data(check=False)

		#stream.close()
		if len(data.shape) == 1:
			# One dimensional stream
			return {"data": data.flatten().tolist(), "width": 1, "height": data.shape[0], "min": min_value,
					"max": max_value}
		else:
			return {"data": data.flatten().tolist(), "width": data.shape[1], "height": data.shape[0], "min": min_value, "max": max_value}

	else:
		return {"data": 0, "width": 0, "height": 0, "min": 0, "max": 0}


def get_stream_data(shm_stream, name, min_value, max_value):
	"""
	Reads and already open shm_stream, after having verified that the stream with that name exists.

	:param shm_stream:
	:param name:
	:param min_value:
	:param max_value:
	:return:
	"""
	exists, stream_path = check_stream(name)

	if exists:
		try:
			data = shm_stream.get_data(check=False)
			list = data.flatten().tolist()
					#stream.close()
			if len(data.shape) == 1:
				# One dimensional stream
				width = 1
				height = data.shape[0]
			else:
				width =  data.shape[1]
				height = data.shape[0]
			return {"data": list, "width": width, "height": height, "min": min(list), "max": max(list)}
		except:
			return {"data": 0, "width": 0, "height": 0, "min": 0, "max": 0}
	else:
		return {"data": 0, "width": 0, "height": 0, "min": 0, "max": 0}


def streams(realData=True):
	if not realData:
		# Returning fake streams for testing purposes
		return fake_data.fake_streams()
	else:
		stream_list = {}

		stream_list["nuvu_stream"] = _get_stream("nuvu_stream", 0, 2**16-1)
		stream_list["shwfs_slopes"] = _get_stream("shwfs_slopes", -2, 2)
		stream_list["dm01disp"] = _get_stream("dm01disp", -1.75, 1.75)
		stream_list["shwfs_slopes_flux"] = _get_stream("shwfs_slopes_flux", 0, 4*(2**16-1))
		stream_list["aol1_mgainfact"] = _get_stream("aol1_mgainfact", 0, 1)
		##streams["aol1_modeval"] = _get_stream("aol1_modeval", -1.75, 1.75) #TODO: uncomment when modal control is working

		return stream_list


def telemetry_save(stream_list):
	telemetry_data = {}

	# Create the in-memory "file"
	#temp_out = io.StringIO()

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
		if stream_list['nuvu_stream'] is None:
			stream_list['nuvu_stream'] = SHM("nuvu_raw")

		stream_keywords = stream_list['nuvu_stream'].get_keywords()

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

	pixel_scale = 5.7929690265142/5 # APO-Q-P240-R8,6 FOV per subap / pixels_per_subap

	if shwfs_exists:
		if stream_list['fps_slopes'] is None:
			stream_list['fps_slopes'] = fps("shwfs_process")

		# Check if it's running
		if stream_list['fps_slopes'].RUNrunning==1:
			telemetry_data["slopes_flux_subaperture"] = stream_list['fps_slopes'].get_param_value_float('flux_subaperture')
			telemetry_data["slopes_residual_pix"]     = stream_list['fps_slopes'].get_param_value_float('residual')
			telemetry_data["slopes_residual_arcsec"]  = stream_list['fps_slopes'].get_param_value_float('residual')*pixel_scale

	# Tip/tilt stream
	#check if fps exists and is running
	tt_exists, tt_fps_path = check_stream("dm02disp")

	if tt_exists:
		if stream_list['tt_stream'] is None:
			stream_list['tt_stream'] = SHM("dm02disp")
			#stream_list['tt_stream'].close()
		#else:
			#stream_list['tt_stream'] = SHM("dm02disp")

		# Check turned off to prevent timeout. Data may be obsolete
		tt_data = stream_list['tt_stream'].get_data(check=False)


		telemetry_data["pi_tip"] = float(tt_data[0])
		telemetry_data["pi_tilt"] = float(tt_data[1])

	# looopRUN process
	#check if fps exists and is running
	looprun_exists, looprun_fps_path = check_fps("loopRUN-1")

	if looprun_exists:
		if stream_list['loopRUN'] is None:
			stream_list['loopRUN'] = fps("loopRUN-1")

		# Check if it's running
		if stream_list['loopRUN'].RUNrunning==1:
			telemetry_data["loop_gain"] = stream_list['loopRUN'].get_param_value_float('loopgain')
			telemetry_data["loop_mult"] = stream_list['loopRUN'].get_param_value_float('loopmult')
			# loopOn 0 = OFF, 1 = ON
			telemetry_data["loop_on"]  = stream_list['loopRUN'].get_param_value_int('loopON')
			if telemetry_data["loop_on"] == 1:
				telemetry_data["loop_on"] = 'ON'
			elif telemetry_data["loop_on"] == 0:
				telemetry_data["loop_on"] = 'OFF'

	database.store_telemetry(telemetry_data)

	#return nuvu_stream, tt_stream, fps_slopes


def wfs_illumination_count(wfs_threshold):
	"""
	Function reads the nuvu stream and return the summed flux in each subaperture

	:return:  subaprtures summed flux
	"""

	# TODO implement masking prodedure in order to only consider usfeul subaps

	shwfs_stream = _get_stream("shwfs_slopes_flux", 0, 4*(2**16-1))

	shwfs_array = np.array(shwfs_stream['data'])

	illuminated_pupil_count = (shwfs_array > wfs_threshold).sum()

	#stream.close()

	#TODO reject subaps out of centering zone

	return illuminated_pupil_count
