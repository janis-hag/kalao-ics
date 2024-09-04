import sys
import time

import numpy as np

from astropy.io import fits

import matplotlib.patches as patches
import matplotlib.pyplot as plt

from kalao.common import kmath, starfinder

if len(sys.argv) == 1:
    rng = np.random.default_rng()

    frame = np.zeros((1024, 1024), dtype=np.float32)
    Y, X = np.mgrid[0:1024, 0:1024]

    # Add stars
    for i in range(5):
        x = rng.uniform(50, 1024 - 50)
        y = rng.uniform(50, 1024 - 50)
        peak = rng.uniform(100, 3000)
        stddev = rng.uniform(2, 30)

        frame += kmath.gaussian_2d_rotated(X, Y, x, y, stddev, stddev,
                                           0 / 180 * np.pi, peak)

    frame = rng.poisson(frame).astype(np.float64)

    # Add dead pixels
    for i in range(10):
        x = round(rng.uniform(50, 1024 - 50))
        y = round(rng.uniform(50, 1024 - 50))

        frame[y, x] = 0

    # Add stuck pixels
    for i in range(10):
        x = round(rng.uniform(50, 1024 - 50))
        y = round(rng.uniform(50, 1024 - 50))

        frame[y, x] = 65535

    # Add hot pixels
    for i in range(10):
        x = round(rng.uniform(50, 1024 - 50))
        y = round(rng.uniform(50, 1024 - 50))
        v = round(rng.uniform(10, 4000))

        frame[y, x] += v

    frame += rng.normal(1000, 20, size=frame.shape)

    frame = np.clip(np.rint(frame), 0, 2**16 - 1).astype(np.uint16)
    frames = [frame]
else:
    frames = []
    for i in range(1, len(sys.argv)):
        frames.append(fits.getdata(sys.argv[i]))

for i, frame in enumerate(frames):
    if i + 1 < len(sys.argv):
        title = f'Frame {i} - {sys.argv[i + 1]}'
    else:
        title = f'Frame {i}'

    print(title)

    plt.figure()
    plt.title(title)
    fig = plt.gcf()
    ax = fig.gca()

    plt.imshow(
        frame,
        norm='log')  # , vmin=np.nanmin(frame_nan), vmax=np.nanmax(frame_nan))

    start = time.monotonic()
    stars, bad_pixels = starfinder.find_stars_and_bad_pixels(frame)
    print('Time to find stars:', time.monotonic() - start)

    for star in stars:
        plt.plot(star.x, star.y, 'r+')
        ax.add_patch(
            patches.Ellipse((star.x, star.y), star.fwhm_w, star.fwhm_h,
                            angle=star.fwhm_angle, edgecolor='r',
                            facecolor='#ffffff00'))

    start = time.monotonic()
    stars, bad_pixels = starfinder.find_stars_and_bad_pixels(
        frame, method='moments')
    print('Time to find stars:', time.monotonic() - start)

    for star in stars:
        plt.plot(star.x, star.y, 'b+')
        ax.add_patch(
            patches.Ellipse((star.x, star.y), star.fwhm_w, star.fwhm_h,
                            angle=star.fwhm_angle, edgecolor='b',
                            facecolor='#ffffff00'))

    # frame_nan = frame.astype(np.float64)
    # frame_nan[bad_pixels] = np.nan

    # plt.plot(bad_pixels[:, 1], bad_pixels[:, 0], 'g+')

plt.show()
