#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov 18 16:53:39 2020

@author: janis
"""

import FLI
from microscope.filterwheels import thorlabs
from astropy.io import fits
import datetime
import time

# clear griz, hole

fw = thorlabs.ThorlabsFW102C(com='/dev/ttyUSB0')
fw.enable()
time.sleep(2)
fw.initialize()
time.sleep(2)
fw.set_position(0)
time.sleep(6)
fw.get_position()

cam = FLI.USBCamera.find_devices()[0]
cam.get_info()
cam.get_temperature()
cam.set_temperature(-30)
cam.set_exposure(100)
img = cam.take_photo()


def take_picture(dit=100):
    det_temp = cam.get_temperature()
    print('CCD temperature: ' + str(det_temp))
    cam.set_exposure(dit)
    filter_number = fw.get_position()
    print('Filter position: ' + str(filter_number))
    hdr = fits.Header()
    hdr['INST'] = 'KalAO'
    hdr['DIT'] = dit
    hdr['FILTN'] = filter_number
    hdr['DET_TEMP'] = det_temp
    frame = cam.take_photo()
    hdu = fits.PrimaryHDU(data=frame, header=hdr)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H.%M.%S")
    hdu.writeto('KALAO.' + timestamp + '.fits')
