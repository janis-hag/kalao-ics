#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : fli_psf.py
# @Date : 2021-02-10-13-43
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg
"""
fli_psf.py is part of the KalAO Instrument Control Software
(KalAO-ICS).
"""

import numpy as np
import time
import matplotlib

matplotlib.use('GTK3Agg')
from matplotlib import pyplot as plt

sys.path.append('../kalao')

import FLI

dit = 1

# def run_doblit(niter=1000, doblit=True):
#     """
#     Display the simulation using matplotlib, optionally using blit for speed
#     """
#
#     fig, ax = plt.subplots(1, 1)
#     ax.set_aspect('equal')
#     ax.set_xlim(0, 255)
#     ax.set_ylim(0, 255)
#     ax.hold(True)
#
#     take_picture..
#
#     plt.show(False)
#     plt.draw()
#
#     if doblit:
#         # cache the background
#         background = fig.canvas.copy_from_bbox(ax.bbox)
#
#     points = ax.plot(x, y, 'o')[0]
#     tic = time.time()
#
#     for ii in xrange(niter):
#
#         # update the xy data
#         x, y = rw.next()
#         points.set_data(x, y)
#
#         if doblit:
#             # restore background
#             fig.canvas.restore_region(background)
#
#             # redraw just the points
#             ax.draw_artist(points)
#
#             # fill in the axes rectangle
#             fig.canvas.blit(ax.bbox)
#
#         else:
#             # redraw everything
#             fig.canvas.draw()
#
#     plt.close(fig)
#     print "Blit = %s, average FPS: %.2f" % (
#         str(doblit), niter / (time.time() - tic))


def run(cam):

    fig, ax = plt.subplots(1, 1)
    ax.set_aspect('equal')
    ax.set_xlim(525, 550)
    ax.set_ylim(525, 550)
    ax.hold(True)

    cam.set_exposure(dit)
    img = cam.take_photo()

    plt.show(False)
    plt.draw()

    frame = ax.imshow(img)[0]

    while True:
        cam.set_exposure(dit)
        img = cam.take_photo()
        frame.set_data(img)
        fig.canvas.draw()
        time.sleep(0.5)


# def take_picture(dit=100):
#     det_temp = cam.get_temperatures()
#     print('CCD temperature: '+str(det_temp))
#     cam.set_exposure(dit)
#     filter_number = fw.get_position()
#     print('Filter position: '+str(filter_number))
#     hdr = fits.Header()
#     hdr['INST'] = 'KalAO'
#     hdr['DIT'] = dit
#     hdr['FILTN'] = filter_number
#     hdr['DET_TEMP'] = det_temp
#     frame = cam.take_photo()
#     hdu = fits.PrimaryHDU(data=frame, header=hdr)
#     timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H.%M.%S")
#     hdu.writeto('KALAO.' + timestamp + '.fits')

if __name__ == '__main__':
    cam = FLI.USBCamera.find_devices()[0]
    cam.get_info()
    cam.get_temperatures()
    cam.set_temperature(-30)
    cam.set_exposure(1)
    run(cam)
    #run(doblit=False)
    #run(doblit=True)
