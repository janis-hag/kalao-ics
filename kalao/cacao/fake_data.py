import math
import random
from datetime import datetime, timezone

debug = False

def fake_streams():
	streams = {}

	if debug:
		import matplotlib.pyplot as plt
		import numpy as np

		fig, axs = plt.subplots(2, 2)

	# Fake WFS
	rows = 64
	cols = 64
	min = 0
	max = 65536
	noise = 2500
	nuvustream_full = [0]*rows*cols

	null = [0,10,110,120]

	for i in range(11):
		for j in range(11):
			if i*11+j in null:
				continue

			nuvustream_full[(5*i+2+4)*cols+(5*j+2+4)] = (max-min) * 1  + random.gauss(0, noise)
			nuvustream_full[(5*i+2+4)*cols+(5*j+3+4)] = (max-min) * 1  + random.gauss(0, noise)
			nuvustream_full[(5*i+3+4)*cols+(5*j+2+4)] = (max-min) * 1  + random.gauss(0, noise)
			nuvustream_full[(5*i+3+4)*cols+(5*j+3+4)] = (max-min) * 1  + random.gauss(0, noise)

			nuvustream_full[(5*i+1+4)*cols+(5*j+2+4)] = (max-min) * 0.2  + random.gauss(0, noise)
			nuvustream_full[(5*i+1+4)*cols+(5*j+3+4)] = (max-min) * 0.2  + random.gauss(0, noise)

			nuvustream_full[(5*i+2+4)*cols+(5*j+1+4)] = (max-min) * 0.2  + random.gauss(0, noise)
			nuvustream_full[(5*i+3+4)*cols+(5*j+1+4)] = (max-min) * 0.2  + random.gauss(0, noise)

			nuvustream_full[(5*i+2+4)*cols+(5*j+4+4)] = (max-min) * 0.2  + random.gauss(0, noise)
			nuvustream_full[(5*i+3+4)*cols+(5*j+4+4)] = (max-min) * 0.2  + random.gauss(0, noise)

			nuvustream_full[(5*i+4+4)*cols+(5*j+2+4)] = (max-min) * 0.2  + random.gauss(0, noise)
			nuvustream_full[(5*i+4+4)*cols+(5*j+3+4)] = (max-min) * 0.2  + random.gauss(0, noise)

	streams["nuvustream_full"] = {"data": nuvustream_full, "width": cols, "height": rows, "min": min, "max": max}

	if debug:
		axs[0, 0].imshow(np.array(nuvustream_full).reshape(rows, cols), cmap='gray')

	# Fake linear slopes
	rows = 11
	cols = 22
	min = -1
	max = 1
	noise = 0.03
	shwfs_slopes = [0]*rows*cols

	null = [0,10,11,21,220,230,231,241]

	max_x = (rows-1)
	max_y = (cols//2-1)

	for i in range(rows):
		for j in range(cols//2):
			shwfs_slopes[i*cols+j]         = (max-min) * (i/max_x) + min + random.gauss(0, noise)
			shwfs_slopes[i*cols+j+cols//2] = (max-min) * (j/max_y) + min + random.gauss(0, noise)

	for i in null:
		shwfs_slopes[i] = 0

	streams["shwfs_slopes"] = {"data": shwfs_slopes, "width": cols, "height": rows, "min": min, "max": max}

	if debug:
		axs[0, 1].imshow(np.array(shwfs_slopes).reshape(rows, cols), cmap='gray')

	# Fake focus on the DM
	rows = 12
	cols = 12
	min = -1.75
	max = 1.75
	dm01disp = [0]*rows*cols

	null = [0,11,132,143]

	middle_x = (rows-1)/2
	middle_y = (cols-1)/2
	diag = math.sqrt((middle_x)**2 + (middle_y)**2)

	for i in range(rows):
		for j in range(cols):
			dm01disp[i*cols+j] = (max-min) * (math.sqrt((i-middle_x)**2 + (j-middle_y)**2)/diag) + min + random.gauss(0, noise)

	for i in null:
		dm01disp[i] = 0

	streams["dm01disp"] = {"data": dm01disp, "width": cols, "height": rows, "min": min, "max": max}

	if debug:
		axs[1, 0].imshow(np.array(dm01disp).reshape(rows, cols), cmap='gray')


	# Fake WFS flux
	rows = 11
	cols = 11
	min = 0
	max = 65536*4
	noise = 2500*4
	shwfs_slopes_flux = [0]*rows*cols

	null = [0,10,110,120]

	for i in range(11):
		for j in range(11):
			shwfs_slopes_flux[i*cols+j] = (max-min) * 1 + min + random.gauss(0, noise)

	for i in null:
		shwfs_slopes_flux[i] = 0

	streams["shwfs_slopes_flux"] = {"data": shwfs_slopes_flux, "width": cols, "height": rows, "min": min, "max": max}

	if debug:
		axs[1, 1].imshow(np.array(shwfs_slopes_flux).reshape(rows, cols), cmap='gray')
		plt.show()

	return streams

def fake_measurements_for_db():
	measurements = {}

	measurements["nuvu_temp_ccd"] = -60 + random.gauss(0, 0.05)
	measurements["nuvu_temp_controller"] = 45 + random.gauss(0, 0.05)
	measurements["nuvu_temp_power_supply"] = 44 + random.gauss(0, 0.05)
	measurements["nuvu_temp_fpga"] = 50 + random.gauss(0, 0.05)
	measurements["nuvu_temp_heatsink"] = 19 + random.gauss(0, 0.05)
	measurements["nuvu_emgain"] = 200
	measurements["nuvu_exposuretime"] = 1

	measurements["slopes_max_flux"] = 60000 + random.gauss(0, 2500)
	measurements["slopes_residual"] = 0.05 + random.gauss(0, 0.02)

	measurements["pi_tip"] = 0 + random.gauss(0, 0.5)
	measurements["pi_tilt"] = 0 + random.gauss(0, 0.5)

	return measurements

def fake_measurements():
	timestamp = datetime.now(timezone.utc).timestamp()
	measurements = {}

	for key, value in fake_measurements_for_db().items():
		measurements[key] = {'timestamps': [timestamp], 'values': [value]}

	return measurements

if __name__ == "__main__":
	debug = True

	fake_streams()
