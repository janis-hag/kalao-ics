#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Nathanaël Restori
"""

from pathlib import Path


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

def create_shm_stream(name):

	exists, stream_path = check_stream(name)

	if exists:
		return SHM(str(stream_path))
	else:
		return None
	

def _get_stream(name, min_value, max_value):

	exists, stream_path = check_stream(name)

	if exists:
		shm_stream = SHM(str(stream_path)) #name)
		#shm_stream = SHM(name) #name)
		# Check turned off to prevent timeout. Data may be obsolete
		data = shm_stream.get_data(check=False)

		#stream.close()

		return {"data": data.flatten().tolist(), "width": data.shape[1], "height": data.shape[0], "min": min_value, "max": max_value}

	else:
		return {"data": 0, "width": 0, "height": 0, "min": 0, "max": 0}

def get_stream_data(shm_stream, min_value, max_value):

	data = shm_stream.get_data(check=False)

	return {"data": data.flatten().tolist(), "width": data.shape[1], "height": data.shape[0], "min": min_value, "max": max_value}

def streams(realData=True):
	# TODO remove dirty debug hack
	if True:  #not realData:
		# Returning fake streams for testing purposes
		return fake_data.fake_streams()
	else:

		stream_list = {}

		stream_list["nuvu_stream"] = _get_stream("nuvu_stream", 0, 2**16-1)
		stream_list["shwfs_slopes"] = _get_stream("shwfs_slopes", -2, 2)
		stream_list["dm01disp"] = _get_stream("dm01disp", -1.75, 1.75)
		stream_list["shwfs_slopes_flux"] = _get_stream("shwfs_slopes_flux", 0, 4*(2**16-1))
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

	pixel_scale =	5.7929690265142/5 # APO-Q-P240-R8,6 FOV per subap / pixels_per_subap

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


	database.store_telemetry(telemetry_data)

	#return nuvu_stream, tt_stream, fps_slopes


def wfs_illumination():
	"""
	Function reads the nuvu stream and return the summed flux in each subaperture

	:return:  subaprtures summed flux
	"""

	# TODO implement masking procdedure in order to only consider usfeul subaps

	stream = SHM("nuvu_acquire")
	frame, subapertures = toolbox.get_roi_and_subapertures(stream.get_data(check=True))

	#stream.close()

	subapertures_flux = subapertures.sum(axis=(1, 2))

	#TODO reject subaps out of centering zone

	return subapertures_flux
