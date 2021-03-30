#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Nathanaël Restori
"""

from pyMilk.interfacing.isio_shmlib import SHM
from CacaoProcessTools import fps, FPS_status

from kalao.utils import database

def _get_stream(name, min, max):
	#TODO: check if stream is alive

	stream = SHM(name)
	data = stream.get_data(check=True)

	return {"data": data.flatten().tolist(), "width": data.shape[1], "height": data.shape[0], "min": min, "max": max}

def streams():
	streams = {}

	streams["nuvu_stream"] = _get_stream("nuvu_stream", 0, 2**16-1)
	streams["shwfs_slopes"] = _get_stream("shwfs_slopes", -2, 2)
	streams["dm01disp"] = _get_stream("dm01disp", -1.75, 1.75)
	streams["shwfs_slopes_flux"] = _get_stream("shwfs_slopes_flux", 0, 4*(2**16-1))
	#streams["aol1_modeval"] = _get_stream("aol1_modeval", -1.75, 1.75) #TODO: uncomment when modal control is working

	return streams

def monitoring_save():
	monitoring = {}

	#TODO: check if fps exists and check fps.RUNrunning
	fps_nuvu = fps("nuvu_acquire")

	monitoring["nuvu_temp_ccd"]          = fps_nuvu["nuvu_accquire.temp_ccd"]
	monitoring["nuvu_temp_controller"]   = fps_nuvu["nuvu_accquire.temp_controller"]
	monitoring["nuvu_temp_power_supply"] = fps_nuvu["nuvu_accquire.temp_power_supply"]
	monitoring["nuvu_temp_fpga"]         = fps_nuvu["nuvu_accquire.temp_fpga"]
	monitoring["nuvu_temp_heatsink"]     = fps_nuvu["nuvu_accquire.temp_heatsink"]
	monitoring["nuvu_emgain"]            = fps_nuvu["nuvu_accquire.emgain"]
	monitoring["nuvu_exposuretime"]      = fps_nuvu["nuvu_accquire.exposuretime"]

	fps_slopes = fps("shwfs_process")

	monitoring["slopes_flux_subaperture"] = fps_slopes["shwfs_process.flux_subaperture"]
	monitoring["slopes_residual"]         = fps_slopes["shwfs_process.residual"]

	pi_stream = SHM("dm02disp")
	pi_data = pi_stream.get_data(check=True)

	monitoring["pi_tip"] = pi_data[0]
	monitoring["pi_tilt"] = pi_data[1]

	database.store_monitoring(monitoring)
