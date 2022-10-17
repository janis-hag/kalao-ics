#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Nathanaël Restori
"""

import math
import random
import builtins
from datetime import datetime, timedelta, timezone

from kalao.cacao.toolbox import *
from kalao.utils import kalao_time

def fake_fli_view():
	# image = [random.choices(range(1,100), k=1024) for _ in range(1024)]
	image = np.random.randint(0, high=np.iinfo(np.uint16).max, size=(256,256), dtype=np.uint16)

	return image

def fake_streams():
	streams = {}

	flux = get_wfs_flux_map()
	min_flux = 0.15

	# Fake WFS
	rows = 64
	cols = 64
	min = 50
	max = 2**16-1
	noise = 100
	nuvu_stream = [0]*rows*cols

	for i in range(11):
		for j in range(11):
			nuvu_stream[(5*i+2+4)*cols+(5*j+2+4)] = (flux[i,j]*(max-min) - noise) * 1   + noise + random.gauss(0, noise)
			nuvu_stream[(5*i+2+4)*cols+(5*j+3+4)] = (flux[i,j]*(max-min) - noise) * 1   + noise + random.gauss(0, noise)
			nuvu_stream[(5*i+3+4)*cols+(5*j+2+4)] = (flux[i,j]*(max-min) - noise) * 1   + noise + random.gauss(0, noise)
			nuvu_stream[(5*i+3+4)*cols+(5*j+3+4)] = (flux[i,j]*(max-min) - noise) * 1   + noise + random.gauss(0, noise)

			nuvu_stream[(5*i+1+4)*cols+(5*j+2+4)] = (flux[i,j]*(max-min) - noise) * 0.1 + noise + random.gauss(0, noise)
			nuvu_stream[(5*i+1+4)*cols+(5*j+3+4)] = (flux[i,j]*(max-min) - noise) * 0.1 + noise + random.gauss(0, noise)

			nuvu_stream[(5*i+2+4)*cols+(5*j+1+4)] = (flux[i,j]*(max-min) - noise) * 0.1 + noise + random.gauss(0, noise)
			nuvu_stream[(5*i+3+4)*cols+(5*j+1+4)] = (flux[i,j]*(max-min) - noise) * 0.1 + noise + random.gauss(0, noise)

			nuvu_stream[(5*i+2+4)*cols+(5*j+4+4)] = (flux[i,j]*(max-min) - noise) * 0.1 + noise + random.gauss(0, noise)
			nuvu_stream[(5*i+3+4)*cols+(5*j+4+4)] = (flux[i,j]*(max-min) - noise) * 0.1 + noise + random.gauss(0, noise)

			nuvu_stream[(5*i+4+4)*cols+(5*j+2+4)] = (flux[i,j]*(max-min) - noise) * 0.1 + noise + random.gauss(0, noise)
			nuvu_stream[(5*i+4+4)*cols+(5*j+3+4)] = (flux[i,j]*(max-min) - noise) * 0.1 + noise + random.gauss(0, noise)

	streams["nuvu_stream"] = {"data": nuvu_stream, "width": cols, "height": rows, "min": min, "max": max}

	# Fake WFS flux
	rows = 11
	cols = 11
	min = min*4
	max = max*4
	noise = noise*4
	shwfs_slopes_flux = [0]*rows*cols

	for i in range(rows):
		for j in range(cols):
			shwfs_slopes_flux[i*cols+j] = (flux[i,j]*(max-min) - noise) * 1 + min + noise + random.gauss(0, noise)


	streams["shwfs_slopes_flux"] = {"data": shwfs_slopes_flux, "width": cols, "height": rows, "min": min, "max": max}

	# Fake linear slopes
	rows = 11
	cols = 22
	min = -2
	max = 2
	noise = 0.03
	shwfs_slopes = [0]*rows*cols

	max_x = (rows-1)
	max_y = (cols//2-1)

	for i in range(rows):
		for j in range(cols//2):
			if flux[i,j] < min_flux:
				continue

			shwfs_slopes[i*cols+j]         = (max-min - noise) * (i/max_x) + min + noise + random.gauss(0, noise)
			shwfs_slopes[i*cols+j+cols//2] = (max-min - noise) * (j/max_y) + min + noise + random.gauss(0, noise)

	streams["shwfs_slopes"] = {"data": shwfs_slopes, "width": cols, "height": rows, "min": min, "max": max}

	# Fake set_focus on the DM
	rows = 12
	cols = 12
	min = -1.75
	max = 1.75
	noise = 0.03
	dm01disp = [0]*rows*cols

	middle_x = (rows-1)/2
	middle_y = (cols-1)/2
	diag = math.sqrt((5.5)**2 + (1.5)**2) # This is the farthest non-maxed pixel

	for i in range(rows):
		for j in range(cols):
			max_flux = 0

			act_index = get_actuator_1d(i, j)
			for subap in get_subapertures_around_actuator(act_index):
				if get_subaperture_2d(subap) != (None, None):
						max_flux = builtins.max(max_flux, flux[get_subaperture_2d(subap)])

			if max_flux < min_flux:
				dm01disp[i*cols+j] = max
			else:
				dm01disp[i*cols+j] = (max-min - noise) * (math.sqrt((i-middle_x)**2 + (j-middle_y)**2)/diag) + min + noise + random.gauss(0, noise)

	streams["dm01disp"] = {"data": dm01disp, "width": cols, "height": rows, "min": min, "max": max}

	# Fake mode coefficients
	rows = 1
	cols = 121
	min = -1.75
	max = 1.75
	noise = 0.03
	aol1_modeval = [0]*rows*cols

	sign = 1
	tau = 3
	for i in range(cols):
		aol1_modeval[i] = sign * ((max-min)/2 - 2*noise) * math.exp(-i/tau) + (max+min)/2 + random.gauss(0, noise)
		sign *= -1

	streams["aol1_modeval"] = {"data": aol1_modeval, "width": cols, "height": rows, "min": min, "max": max}

	return streams


def fake_telemetry_for_db():

	time_utc = kalao_time.now()

	telemetry = {}

	telemetry["nuvu_temp_ccd"] = {"time_utc": [time_utc], "values": [-60 + random.gauss(0, 0.05)]}
	telemetry["nuvu_temp_controller"] = {"time_utc": [time_utc], "values": [45 + random.gauss(0, 0.05)]}
	telemetry["nuvu_temp_power_supply"] = {"time_utc": [time_utc], "values": [45 + random.gauss(0, 0.05)]}
	telemetry["nuvu_temp_fpga"] = {"time_utc": [time_utc], "values": [50 + random.gauss(0, 0.05)]}
	telemetry["nuvu_temp_heatsink"] = {"time_utc": [time_utc], "values": [15 + random.gauss(0, 0.05)]}
	telemetry["nuvu_emgain"] = {"time_utc": [time_utc], "values": [200]}
	telemetry["nuvu_exposuretime"] = {"time_utc": [time_utc], "values": [0.5]}

	telemetry["slopes_flux_subaperture"] = {"time_utc": [time_utc], "values": [2**16-1 - 200 + random.gauss(0, 200)]}
	telemetry["slopes_residual"] = {"time_utc": [time_utc], "values": [0.05 + random.gauss(0, 0.02)]}

	telemetry["pi_tip"] = {"time_utc": [time_utc], "values": [0 + random.gauss(0, 0.5)]}
	telemetry["pi_tilt"] = {"time_utc": [time_utc], "values": [0 + random.gauss(0, 0.5)]}

	telemetry["time_utc"] = {"time_utc": [time_utc], "values": [time_utc]}

	return telemetry


def fake_telemetry():
	time_utc = kalao_time.now()
	telemetry = {}

	for key, value in fake_telemetry_for_db().items():
		telemetry[key] = {'time_utc': [time_utc], 'values': [value]}

	return telemetry


def fake_telemetry_series():
	time_now = kalao_time.now()

	telemetry = {}
	keys = ["pi_tip", "pi_tilt"]

	for key in keys:
		telemetry[key] = {'time_utc': [], 'values': []}

		for i in range(3*3600):
			telemetry[key]['time_utc'].append(time_now - timedelta(seconds=i))
			telemetry[key]['values'].append(fake_telemetry_for_db()[key])

	return telemetry

def fake_latest_obs_log_entry():

	time_string = datetime.today().isoformat(timespec='milliseconds')
	key_name = 'TEST'
	record_text = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua'
	formated_entry_text = time_string+' '+key_name+': '+record_text

	return formated_entry_text

if __name__ == "__main__":
	import matplotlib.pyplot as plt
	import numpy as np

	streams = fake_streams()

	fig, axs = plt.subplots(2, 2)

	def _add_stream(i, j, name):
		axs[i, j].imshow(np.array(streams[name]["data"]).reshape(streams[name]["height"], streams[name]["width"]), cmap='gray')

	_add_stream(0, 0, "nuvu_stream")
	_add_stream(0, 1, "shwfs_slopes_flux")
	_add_stream(1, 0, "shwfs_slopes")
	_add_stream(1, 1, "dm01disp")

	plt.show()
