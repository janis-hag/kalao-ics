#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Nathanaël Restori
"""

from pyMilk.interfacing.isio_shmlib import SHM
from CacaoProcessTools import fps, FPS_status

from kalao.utils import database
from kalao.cacao import fake_data

def _get_stream(name, min, max):
	#TODO: check if stream is alive
	# Return empty stream if not existing

	stream = SHM(name)
	data = stream.get_data(check=True)

	return {"data": data.flatten().tolist(), "width": data.shape[1], "height": data.shape[0], "min": min, "max": max}

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

	#TODO: check if fps exists and check fps.RUNrunning
	fps_nuvu = fps("nuvu_acquire")

	telemetry["nuvu_temp_ccd"]          = fps_nuvu["nuvu_accquire.temp_ccd"]
	telemetry["nuvu_temp_controller"]   = fps_nuvu["nuvu_accquire.temp_controller"]
	telemetry["nuvu_temp_power_supply"] = fps_nuvu["nuvu_accquire.temp_power_supply"]
	telemetry["nuvu_temp_fpga"]         = fps_nuvu["nuvu_accquire.temp_fpga"]
	telemetry["nuvu_temp_heatsink"]     = fps_nuvu["nuvu_accquire.temp_heatsink"]
	telemetry["nuvu_emgain"]            = fps_nuvu["nuvu_accquire.emgain"]
	telemetry["nuvu_exposuretime"]      = fps_nuvu["nuvu_accquire.exposuretime"]

	fps_slopes = fps("shwfs_process")

	telemetry["slopes_flux_subaperture"] = fps_slopes["shwfs_process.flux_subaperture"]
	telemetry["slopes_residual"]         = fps_slopes["shwfs_process.residual"]

	pi_stream = SHM("dm02disp")
	pi_data = pi_stream.get_data(check=True)

	telemetry["pi_tip"] = pi_data[0]
	telemetry["pi_tilt"] = pi_data[1]

	database.get_ao_telemetry(telemetry)
