#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Nathanaël Restori
"""

import builtins
import math
import random
from datetime import datetime, timedelta

from kalao.cacao import toolbox
from kalao.utils import kalao_math, kalao_time


def fake_streams():
    streams = {}

    flux = toolbox.get_wfs_flux_map()
    min_flux = 0.15

    # Fake WFS
    rows = 64
    cols = 64
    min = 50
    max = 2**16 - 1
    noise = 100
    nuvu_stream = [0] * rows * cols

    # yapf: disable
    for i in range(11):
        for j in range(11):
            nuvu_stream[(5 * i + 2 + 4) * cols + (5 * j + 2 + 4)] = (flux[i, j] * (max - min) - noise) * 1 + noise + random.gauss(0, noise)
            nuvu_stream[(5 * i + 2 + 4) * cols + (5 * j + 3 + 4)] = (flux[i, j] * (max - min) - noise) * 1 + noise + random.gauss(0, noise)
            nuvu_stream[(5 * i + 3 + 4) * cols + (5 * j + 2 + 4)] = (flux[i, j] * (max - min) - noise) * 1 + noise + random.gauss(0, noise)
            nuvu_stream[(5 * i + 3 + 4) * cols + (5 * j + 3 + 4)] = (flux[i, j] * (max - min) - noise) * 1 + noise + random.gauss(0, noise)
            nuvu_stream[(5 * i + 1 + 4) * cols + (5 * j + 2 + 4)] = (flux[i, j] * (max - min) - noise) * 0.1 + noise + random.gauss(0, noise)
            nuvu_stream[(5 * i + 1 + 4) * cols + (5 * j + 3 + 4)] = (flux[i, j] * (max - min) - noise) * 0.1 + noise + random.gauss(0, noise)
            nuvu_stream[(5 * i + 2 + 4) * cols + (5 * j + 1 + 4)] = (flux[i, j] * (max - min) - noise) * 0.1 + noise + random.gauss(0, noise)
            nuvu_stream[(5 * i + 3 + 4) * cols + (5 * j + 1 + 4)] = (flux[i, j] * (max - min) - noise) * 0.1 + noise + random.gauss(0, noise)
            nuvu_stream[(5 * i + 2 + 4) * cols + (5 * j + 4 + 4)] = (flux[i, j] * (max - min) - noise) * 0.1 + noise + random.gauss(0, noise)
            nuvu_stream[(5 * i + 3 + 4) * cols + (5 * j + 4 + 4)] = (flux[i, j] * (max - min) - noise) * 0.1 + noise + random.gauss(0, noise)
            nuvu_stream[(5 * i + 4 + 4) * cols + (5 * j + 2 + 4)] = (flux[i, j] * (max - min) - noise) * 0.1 + noise + random.gauss(0, noise)
            nuvu_stream[(5 * i + 4 + 4) * cols + (5 * j + 3 + 4)] = (flux[i, j] * (max - min) - noise) * 0.1 + noise + random.gauss(0, noise)
    # yapf: enable

    streams["nuvu_stream"] = {
            "data": nuvu_stream,
            "width": cols,
            "height": rows,
            "min": min,
            "max": max,
            "min_th": min,
            "max_th": max,
    }

    # Fake WFS flux
    rows = 11
    cols = 11
    min = min * 4
    max = max * 4
    noise = noise * 4
    shwfs_slopes_flux = [0] * rows * cols

    # yapf: disable
    for i in range(rows):
        for j in range(cols):
            shwfs_slopes_flux[i * cols + j] = (flux[i, j] * (max - min) - noise) * 1 + min + noise + random.gauss(0, noise)
    # yapf: enable

    streams["shwfs_slopes_flux"] = {
            "data": shwfs_slopes_flux,
            "width": cols,
            "height": rows,
            "min": min,
            "max": max,
            "min_th": min,
            "max_th": max,
    }

    # Fake linear slopes
    rows = 11
    cols = 22
    min = -2
    max = 2
    noise = 0.03
    shwfs_slopes = [0] * rows * cols

    max_x = (rows - 1)
    max_y = (cols // 2 - 1)

    # yapf: disable
    for i in range(rows):
        for j in range(cols // 2):
            if flux[i, j] < min_flux:
                continue

            shwfs_slopes[i * cols + j] = (max - min - noise) * (i / max_x) + min + noise + random.gauss(0, noise)
            shwfs_slopes[i * cols + j + cols // 2] = (max - min - noise) * (j / max_y) + min + noise + random.gauss(0, noise)
    # yapf: enable

    streams["shwfs_slopes"] = {
            "data": shwfs_slopes,
            "width": cols,
            "height": rows,
            "min": min,
            "max": max,
            "min_th": min,
            "max_th": max,
    }

    # Fake focus on the DM
    rows = 12
    cols = 12
    min = -1.75
    max = 1.75
    noise = 0.03
    dm01disp = [0] * rows * cols

    middle_x = (rows - 1) / 2
    middle_y = (cols - 1) / 2
    diag = math.sqrt(
            (5.5)**2 + (1.5)**2)  # This is the farthest non-maxed pixel

    # yapf: disable
    for i in range(rows):
        for j in range(cols):
            max_flux = 0

            act_index = toolbox.get_actuator_1d(i, j)
            for subap in toolbox.get_subapertures_around_actuator(act_index):
                if toolbox.get_subaperture_2d(subap) != (None, None):
                    max_flux = builtins.max(max_flux, flux[toolbox.get_subaperture_2d(subap)])

            if max_flux < min_flux:
                dm01disp[i * cols + j] = 0
            else:
                dm01disp[i * cols + j] = (max - min - noise) * (math.sqrt((i - middle_x)**2 + (j - middle_y)**2) / diag) + min + noise + random.gauss(0, noise)
    # yapf: enable

    streams["dm01disp"] = {
            "data": dm01disp,
            "width": cols,
            "height": rows,
            "min": min,
            "max": max,
            "min_th": min,
            "max_th": max,
    }

    # Fake mode coefficients
    rows = 1
    cols = 121
    min = -1.75
    max = 1.75
    noise = 0.03
    aol1_modeval = [0] * rows * cols

    sign = 1
    tau = 3

    # yapf: enable
    for i in range(cols):
        aol1_modeval[i] = sign * ((max - min) / 2 - 2 * noise) * math.exp(
                -i / tau) + (max + min) / 2 + random.gauss(0, noise)
        sign *= -1
    # yapf: disable

    streams["aol1_modeval"] = {
            "data": aol1_modeval,
            "width": cols,
            "height": rows,
            "min": min,
            "max": max,
            "min_th": min,
            "max_th": max,
    }

    return streams


def fake_tip_tilt(nb_points):
    min = -0.25
    max = 0.25

    time_now = kalao_time.now()

    telemetry = {}
    keys = ["pi_tip", "pi_tilt"]

    for key in keys:
        telemetry[key] = []

        for i in range(nb_points):
            telemetry[key].append({'value': random.gauss(min, max) , 'timestamp': time_now - timedelta(seconds=i)})

    return telemetry


def fake_fli_image(size=(1024, 1024)):
    x, y = np.mgrid[0:size[0], 0:size[1]].astype(np.float32)

    x -= (size[0] - 1) / 2
    y -= (size[1] - 1) / 2

    image = np.random.normal(1000, 10, size=size)
    image += kalao_math.gaussian_2d_rotated(x, y, 0, 0, 10, 10, 0, 10000, 0)

    return image


def fake_all_last_telemetry():

    timestamp = kalao_time.now()

    telemetry = {}

    # NuVu
    telemetry["nuvu_temp_ccd"] = [{
            "timestamp": timestamp,
            "value": -60 + random.gauss(0, 0.05)
    }]
    telemetry["nuvu_temp_controller"] = [{
            "timestamp": timestamp,
            "value": 45 + random.gauss(0, 0.05)
    }]
    telemetry["nuvu_temp_power_supply"] = [{
            "timestamp": timestamp,
            "value": 45 + random.gauss(0, 0.05)
    }]
    telemetry["nuvu_temp_fpga"] = [{
            "timestamp": timestamp,
            "value": 50 + random.gauss(0, 0.05)
    }]
    telemetry["nuvu_temp_heatsink"] = [{
            "timestamp": timestamp,
            "value": 15 + random.gauss(0, 0.05)
    }]
    telemetry["nuvu_emgain"] = [{"timestamp": timestamp, "value": 200}]
    telemetry["nuvu_exposuretime"] = [{"timestamp": timestamp, "value": 0.5}]

    # Slopes
    telemetry["slopes_flux_subaperture"] = [{
            "timestamp": timestamp,
            "value": 2**16 - 1 - 200 + random.gauss(0, 200)
    }]
    telemetry["slopes_residual"] = [{
            "timestamp": timestamp,
            "value": 0.05 + random.gauss(0, 0.02)
    }]

    # Tip-Tilt
    telemetry["pi_tip"] = [{
            "timestamp": timestamp,
            "value": 0 + random.gauss(0, 0.5)
    }]
    telemetry["pi_tilt"] = [{
            "timestamp": timestamp,
            "value": 0 + random.gauss(0, 0.5)
    }]

    return telemetry


def fake_latest_obs_log_entry():
    time_string = datetime.today().isoformat(timespec='milliseconds')
    key_name = 'TEST'
    record_text = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua'
    formated_entry_text = time_string + ' ' + key_name + ': ' + record_text

    return formated_entry_text


if __name__ == "__main__":
    import numpy as np

    import matplotlib.pyplot as plt

    streams = fake_streams()

    fig, axs = plt.subplots(2, 3)

    def _add_stream(i, j, name):
        axs[i, j].imshow(
                np.array(streams[name]["data"]).reshape(
                        streams[name]["height"], streams[name]["width"]),
                cmap='gray')

    _add_stream(0, 0, "nuvu_stream")
    _add_stream(0, 1, "shwfs_slopes_flux")
    _add_stream(1, 0, "shwfs_slopes")
    _add_stream(1, 1, "dm01disp")

    axs[0, 2].imshow(fake_fli_image((1024, 1024)), cmap='gray')
    axs[1, 2].imshow(fake_fli_image((256, 256)), cmap='gray')

    plt.show()
