#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Nathanaël Restori
"""

import math
import random
from datetime import datetime, timedelta, timezone

from kalao.cacao.toolbox import *

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

	# Fake focus on the DM
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
						max_flux = __builtins__.max(max_flux, flux[get_subaperture_2d(subap)])

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

def fake_monitoring_for_db():
	monitoring = {}

	monitoring["nuvu_temp_ccd"] = -60 + random.gauss(0, 0.05)
	monitoring["nuvu_temp_controller"] = 45 + random.gauss(0, 0.05)
	monitoring["nuvu_temp_power_supply"] = 45 + random.gauss(0, 0.05)
	monitoring["nuvu_temp_fpga"] = 50 + random.gauss(0, 0.05)
	monitoring["nuvu_temp_heatsink"] = 15 + random.gauss(0, 0.05)
	monitoring["nuvu_emgain"] = 200
	monitoring["nuvu_exposuretime"] = 0.5

	monitoring["slopes_flux_subaperture"] = 2**16-1 - 200 + random.gauss(0, 200)
	monitoring["slopes_residual"] = 0.05 + random.gauss(0, 0.02)

	monitoring["pi_tip"] = 0 + random.gauss(0, 0.5)
	monitoring["pi_tilt"] = 0 + random.gauss(0, 0.5)

	return monitoring

def fake_monitoring():
	timestamp = datetime.now(timezone.utc).timestamp()
	monitoring = {}

	for key, value in fake_monitoring_for_db().items():
		monitoring[key] = {'timestamps': [timestamp], 'values': [value]}

	return monitoring

def fake_monitoring_series():
	timestamp = datetime.now(timezone.utc).timestamp()
	monitoring = {}
	keys = ["pi_tip", "pi_tilt"]

	for key in keys:
		monitoring[key] = {'timestamps': [], 'values': []}

		for i in range(3*3600):
			monitoring[key]['timestamps'].append(timestamp-i)
			monitoring[key]['values'].append(fake_monitoring_for_db()[key])

	return monitoring

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


