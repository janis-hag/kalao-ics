#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Nathanaël Restori
"""

import os
import time

import numpy as np
from scipy import ndimage

from pyqtgraph.Qt import QtCore
import pyqtgraph as pg

from pyMilk.interfacing.isio_shmlib import SHM

from kalao.cacao.toolbox import *

def clamp(n, minn, maxn):
	if n < minn:
		return minn
	elif n > maxn:
		return maxn
	else:
		return n

def center_of_mass(array):
	x, y = ndimage.measurements.center_of_mass(array)
	x = clamp(x+0.5, 0, array.shape[0])
	y = clamp(y+0.5, 0, array.shape[1])

	return (x,y)

##### What to display/poke
tiptilt_subap_indexes = (0, 10, 110, 120, 60)

dm_actuators_poke = (50, 53, 86, 89)
dm_actuators_amplitude = 3.5*0.2
dm_actuators_amplitude_change = 3.5*0.05
dm_actuators_amplitude_max = 1.5
dm_wait_after_poke = 15e-3

dm_subap_indexes = ()
for i in dm_actuators_poke:
	dm_subap_indexes += get_subapertures_around_actuator(i)

##### General configuration

FLAT = 0
DOWN = 1
UP = 2

HORI = 0
VERT = 1

GREY = '#eff0f1'
RED = '#ed1515'
ORANGE = '#f67400'
GREEN = '#11d116'
BLUE = '#1d99f3'
YELLOW = '#fdbc4b'

display = 0
frame = {}
subapertures = {}

loop = True

def keyPressed(event):
	global loop, display, dm_actuators_amplitude

	if event.key() == QtCore.Qt.Key_Q or event.key() == QtCore.Qt.Key_Escape:
		loop = False
	elif event.key() == QtCore.Qt.Key_Space:
		display = (display + 1) %3
	elif event.key() == QtCore.Qt.Key_Minus:
		dm_actuators_amplitude -= dm_actuators_amplitude_change

		if dm_actuators_amplitude < 0:
			dm_actuators_amplitude = 0

	elif event.key() == QtCore.Qt.Key_Plus:
		dm_actuators_amplitude += dm_actuators_amplitude_change

		if dm_actuators_amplitude > dm_actuators_amplitude_max:
			dm_actuators_amplitude = dm_actuators_amplitude_max

pg.setConfigOption('background', GREY)
pg.setConfigOption('imageAxisOrder', 'row-major')
pg.mkQApp()

##### Pupil window
pupil_window = pg.GraphicsLayoutWidget(title="Pupil alignment")
pupil_window.keyPressEvent = keyPressed
pupil_window.show()

pupil_viewbox = pupil_window.addViewBox(row=0, col=0, invertY=True)
pupil_viewbox.setAspectLocked(True)
pupil_imageitem = pg.ImageItem()
pupil_viewbox.addItem(pupil_imageitem)

pupil_text_line_1 = pg.LabelItem("", color=BLUE, bold=True)
pupil_window.addItem(pupil_text_line_1, row=1, col=0)

pupil_text_line_2 = pg.LabelItem("", color=BLUE, bold=True)
pupil_window.addItem(pupil_text_line_2, row=2, col=0)

pupil_flux_top    = range( 12, 20+1,1)
pupil_flux_bottom = range(100,108+1,1)
pupil_flux_left   = range( 12,100+1,11)
pupil_flux_right  = range( 20,108+1,11)

##### Tip-Tilt window
tiptilt_window = pg.GraphicsLayoutWidget(title="Tip-Tilt alignment")
tiptilt_window.keyPressEvent = keyPressed
tiptilt_window.show()

tiptilt_viewbox_topleft = tiptilt_window.addViewBox(row=0,col=0, invertY=True)
tiptilt_viewbox_topright = tiptilt_window.addViewBox(row=0,col=2, invertY=True)
tiptilt_viewbox_bottomleft = tiptilt_window.addViewBox(row=2,col=0, invertY=True)
tiptilt_viewbox_bottomright = tiptilt_window.addViewBox(row=2,col=2, invertY=True)
tiptilt_viewbox_center = tiptilt_window.addViewBox(row=1,col=1, invertY=True)

tiptilt_viewboxes = (tiptilt_viewbox_topleft, tiptilt_viewbox_topright, tiptilt_viewbox_bottomleft, tiptilt_viewbox_bottomright, tiptilt_viewbox_center)
tiptilt_subap_images = ()
tiptilt_crosses = ()
tiptilt_text_inds = ()
tiptilt_text_locs = ()

for viewbox in tiptilt_viewboxes:
	viewbox.setAspectLocked(True)

	tiptilt_subap_image = pg.ImageItem()
	tiptilt_cross_vert = pg.InfiniteLine(angle=90, movable=False, pen=YELLOW)
	tiptilt_cross_hori = pg.InfiniteLine(angle=0, movable=False, pen=YELLOW)
	tiptilt_text_ind = pg.TextItem("", color=RED)
	tiptilt_text_loc = pg.TextItem("", color='k', anchor=(0, 1))
	viewbox.addItem(tiptilt_subap_image)
	viewbox.addItem(tiptilt_cross_vert)
	viewbox.addItem(tiptilt_cross_hori)
	viewbox.addItem(tiptilt_text_ind)
	viewbox.addItem(tiptilt_text_loc)

	tiptilt_subap_images += (tiptilt_subap_image,)
	tiptilt_crosses += ({VERT: tiptilt_cross_vert, HORI: tiptilt_cross_hori},)
	tiptilt_text_inds += (tiptilt_text_ind,)
	tiptilt_text_locs += (tiptilt_text_loc,)


##### DM window
dm_window = pg.GraphicsLayoutWidget(title="DM alignment")
dm_window.keyPressEvent = keyPressed
dm_window.show()

dm_viewboxes = ()

def dm_layout_add_viewboxes(layout):
	dm_viewbox_topleft = layout.addViewBox(row=0, col=0, invertY=True)
	dm_viewbox_topright = layout.addViewBox(row=0, col=1, invertY=True)
	dm_viewbox_bottomleft = layout.addViewBox(row=1, col=0, invertY=True)
	dm_viewbox_bottomright = layout.addViewBox(row=1, col=1, invertY=True)

	global dm_viewboxes
	dm_viewboxes += (dm_viewbox_topleft, dm_viewbox_topright, dm_viewbox_bottomleft, dm_viewbox_bottomright)

dm_layout_topleft = dm_window.addLayout(row=0, col=0)
dm_layout_add_viewboxes(dm_layout_topleft)

dm_layout_topright = dm_window.addLayout(row=0, col=2)
dm_layout_add_viewboxes(dm_layout_topright)

dm_layout_bottomleft = dm_window.addLayout(row=2, col=0)
dm_layout_add_viewboxes(dm_layout_bottomleft)

dm_layout_bottomright = dm_window.addLayout(row=2, col=2)
dm_layout_add_viewboxes(dm_layout_bottomright)

dm_spacing_vert = dm_window.addLayout(row=0, col=1)
dm_spacing_horiz = dm_window.addLayout(row=1, col=0)

dm_window.ci.layout.setColumnStretchFactor(0, 5)
dm_window.ci.layout.setColumnStretchFactor(1, 1)
dm_window.ci.layout.setColumnStretchFactor(2, 5)
dm_window.ci.layout.setRowStretchFactor(0, 5)
dm_window.ci.layout.setRowStretchFactor(1, 1)
dm_window.ci.layout.setRowStretchFactor(2, 5)

dm_subap_images = ()
dm_crosses = ()
dm_text_inds = ()

for viewbox in dm_viewboxes:
	viewbox.setAspectLocked(True)

	dm_subap_image = pg.ImageItem()
	dm_cross_vert_ref = pg.InfiniteLine(angle=90, movable=False, pen=BLUE)
	dm_cross_hori_ref = pg.InfiniteLine(angle=0, movable=False, pen=BLUE)
	dm_cross_vert_down = pg.InfiniteLine(angle=90, movable=False, pen=RED)
	dm_cross_hori_down = pg.InfiniteLine(angle=0, movable=False, pen=RED)
	dm_cross_vert_up = pg.InfiniteLine(angle=90, movable=False, pen=GREEN)
	dm_cross_hori_up = pg.InfiniteLine(angle=0, movable=False, pen=GREEN)
	dm_text_ind = pg.TextItem("", color=RED)
	viewbox.addItem(dm_subap_image)
	viewbox.addItem(dm_cross_vert_ref)
	viewbox.addItem(dm_cross_hori_ref)
	viewbox.addItem(dm_cross_hori_down)
	viewbox.addItem(dm_cross_vert_down)
	viewbox.addItem(dm_cross_hori_up)
	viewbox.addItem(dm_cross_vert_up)
	viewbox.addItem(dm_text_ind)

	dm_subap_images += (dm_subap_image,)
	dm_crosses += ({FLAT: {VERT: dm_cross_vert_ref, HORI: dm_cross_hori_ref},
	                DOWN: {VERT: dm_cross_vert_down, HORI: dm_cross_hori_down},
	                UP: {VERT: dm_cross_vert_up, HORI: dm_cross_hori_up}},)
	dm_text_inds += (dm_text_ind,)

##### Help
warning = "WARNING:<br /><br />'bmc_display', 'nuvu_acquire' and 'DMcomb' must be set-up and running,<br />and the dm flat must be loaded for this tool to work properly"

config = "CONFIG:<br /><br />The following configs are supported:<br />• binning = 1 (will take ROI Start X/Y = 9, ROI End X/Y = 119)<br />• binning = 2 (will take ROI Start X/Y = 4, ROI End X/Y = 60)"

manual = "MANUAL:<br /><br />• Press 'Q' or 'Esc' to exit cleanly (DM cleared)<br />• Press 'Space' to cycle between the different wavefronts<br />• Press 'Plus' to increase poke amplitude<br />• Press 'Minus' to decrease poke amplitude"

print(warning.replace('<br />', ' '))

popup_window = pg.GraphicsLayoutWidget(title="Help", size=(600, 300))
popup_window.keyPressEvent = keyPressed
popup_window.show()

popup_warning = pg.LabelItem(warning, color=ORANGE, bold=True)
popup_warning.setAttr("justify", "left")
popup_window.addItem(popup_warning, row=0, col=0)

popup_config = pg.LabelItem(config, color=GREEN, bold=True)
popup_config.setAttr("justify", "left")
popup_window.addItem(popup_config, row=1, col=0)

popup_manual = pg.LabelItem(manual, color=BLUE, bold=True)
popup_manual.setAttr("justify", "left")
popup_window.addItem(popup_manual, row=2, col=0)

# Open needed streams
nuvu_stream = SHM("nuvu_stream")
dmdisp = SHM("dm01disp10")

dm_array = np.zeros(dmdisp.shape, dmdisp.nptype)

# Add grid to pupil windows
if nuvu_stream.shape == (128,128):
	for i in range(11):
		pupil_viewbox.addItem(pg.InfiniteLine(pos=10*i, angle=90, movable=False, pen=YELLOW))
		pupil_viewbox.addItem(pg.InfiniteLine(pos=10*i, angle=0, movable=False, pen=YELLOW))
elif nuvu_stream.shape == (64,64):
	for i in range(11):
		pupil_viewbox.addItem(pg.InfiniteLine(pos=5*i+1, angle=90, movable=False, pen=YELLOW))
		pupil_viewbox.addItem(pg.InfiniteLine(pos=5*i+5, angle=90, movable=False, pen=YELLOW))
		pupil_viewbox.addItem(pg.InfiniteLine(pos=5*i+1, angle=0, movable=False, pen=YELLOW))
		pupil_viewbox.addItem(pg.InfiniteLine(pos=5*i+5, angle=0, movable=False, pen=YELLOW))

while loop:
	# Do not poke actuators
	for act in dm_actuators_poke:
		dm_array[get_actuator_2d(act)] = 0

	dmdisp.set_data(dm_array, True)
	time.sleep(dm_wait_after_poke)
	frame[FLAT], subapertures[FLAT] = get_roi_and_subapertures(nuvu_stream.get_data(check=True))

	# Poke actuators down
	for act in dm_actuators_poke:
		dm_array[get_actuator_2d(act)] = -dm_actuators_amplitude

	dmdisp.set_data(dm_array, True)
	time.sleep(dm_wait_after_poke)
	frame[DOWN], subapertures[DOWN] = get_roi_and_subapertures(nuvu_stream.get_data(check=True))

	# Poke actuators up
	for act in dm_actuators_poke:
		dm_array[get_actuator_2d(act)] = dm_actuators_amplitude

	dmdisp.set_data(dm_array, True)
	time.sleep(dm_wait_after_poke)
	frame[UP], subapertures[UP] = get_roi_and_subapertures(nuvu_stream.get_data(check=True))

	# Pupil window
	pupil_flux_top_sum = 0
	pupil_flux_bottom_sum = 0
	pupil_flux_left_sum = 0
	pupil_flux_right_sum = 0

	for i in pupil_flux_top:
		pupil_flux_top_sum += np.sum(subapertures[FLAT][i])

	for i in pupil_flux_bottom:
		pupil_flux_bottom_sum += np.sum(subapertures[FLAT][i])

	for i in pupil_flux_left:
		pupil_flux_left_sum += np.sum(subapertures[FLAT][i])

	for i in pupil_flux_right:
		pupil_flux_right_sum += np.sum(subapertures[FLAT][i])

	pupil_text_line_1.setText(f"Top : {pupil_flux_top_sum:.1f}, Bottom : {pupil_flux_bottom_sum:.1f}, Left : {pupil_flux_left_sum:.1f}, Right : {pupil_flux_right_sum:.1f}")
	pupil_text_line_2.setText(f"T/B: {pupil_flux_top_sum/pupil_flux_bottom_sum:.3f} L/R: {pupil_flux_left_sum/pupil_flux_right_sum:.3f}")

	pupil_imageitem.setImage(frame[display])

	# Tip-Tilt window
	for i, subap_image, cross, text_ind, text_loc in zip(tiptilt_subap_indexes, tiptilt_subap_images, tiptilt_crosses, tiptilt_text_inds, tiptilt_text_locs):
		pos = center_of_mass(subapertures[FLAT][i])
		text_ind.setText(f"{i}")
		text_loc.setText(f"({pos[HORI]:.2f},{pos[VERT]:.2f})")
		cross[VERT].setValue(pos[VERT])
		cross[HORI].setValue(pos[HORI])
		subap_image.setImage(subapertures[display][i])

	# DM window
	for i, subap_image, cross, text_ind in zip(dm_subap_indexes, dm_subap_images, dm_crosses, dm_text_inds):
		pos = center_of_mass(subapertures[FLAT][i])
		text_ind.setText(f"{i}")
		cross[FLAT][VERT].setValue(pos[VERT])
		cross[FLAT][HORI].setValue(pos[HORI])

		pos = center_of_mass(subapertures[DOWN][i])
		cross[DOWN][VERT].setValue(pos[VERT])
		cross[DOWN][HORI].setValue(pos[HORI])

		pos = center_of_mass(subapertures[UP][i])
		cross[UP][VERT].setValue(pos[VERT])
		cross[UP][HORI].setValue(pos[HORI])

		subap_image.setImage(subapertures[display][i])

	pg.QtGui.QApplication.processEvents()

# Clear DM before exiting
dm_array = np.zeros(dmdisp.shape, dmdisp.nptype)
dmdisp.set_data(dm_array, True)
