import numpy as np

from PySide2.QtCore import Signal
from PySide2.QtGui import QImage, Qt

from guis.kalao import colormaps


class ArrayToImageMixin():
    colormap = colormaps.BlackBody()

    def prepare_array_for_qimage(self, img, img_min=None, img_max=None):
        if img_min is None:
            img_min = img.min()

        if img_max is None:
            img_max = img.max()

        if np.ma.is_masked(img):
            img = img.filled()

        delta = img_max - img_min
        delta = max(1e-9, delta)

        scale_max = 255
        scale_min = 0

        if self.colormap.has_transparency:
            scale_max -= 1

        if self.colormap.color_saturation_high is not None:
            scale_max -= 0.51

        if self.colormap.color_saturation_low is not None:
            scale_min += 0.51

        rescale = (scale_max-scale_min) / delta
        offset = img_min*rescale - scale_min

        array = img*rescale - offset
        array = np.rint(array).astype(int)
        array = np.clip(array, 0, 255)

        self.img_uint8 = np.require(array, np.uint8, 'C')
        self.image = QImage(self.img_uint8.data, self.img_uint8.shape[1],
                            self.img_uint8.shape[0], self.img_uint8.shape[1],
                            QImage.Format_Indexed8)
        self.image.setColorTable(self.colormap.colormap)


class MinMaxMixin:
    data_min = -np.inf
    data_max = np.inf
    data_unit = ''
    data_scaling = 1
    data_scaling_prev = 1
    data_precision = 0
    data_center_x = 0
    data_center_y = 0

    axis_unit = ''
    axis_scaling = 1
    axis_precision = 0

    def __init__(self):
        self.min_spinbox.valueChanged.connect(self.min_changed)
        self.max_spinbox.valueChanged.connect(self.max_changed)
        self.autoscale_checkbox.stateChanged.connect(self.autoscale_changed)
        self.fullscale_button.clicked.connect(self.fullscale_clicked)

        self.autoscale_changed(self.autoscale_checkbox.checkState())
        self.min_changed(self.min_spinbox.value())
        self.max_changed(self.max_spinbox.value())
        self.update_spinboxes_unit()

    def min_changed(self, d):
        self.data_min = d
        self.max_spinbox.setMinimum(d)

    def max_changed(self, d):
        self.data_max = d
        self.min_spinbox.setMaximum(d)

    def autoscale_changed(self, state):
        self.min_spinbox.setEnabled(state == Qt.Unchecked)
        self.max_spinbox.setEnabled(state == Qt.Unchecked)

    def fullscale_clicked(self, checked):
        self.autoscale_checkbox.setChecked(False)
        self.min_spinbox.setValue(self.stream_info['min'] * self.data_scaling)
        self.max_spinbox.setValue(self.stream_info['max'] * self.data_scaling)

    def update_spinboxes_unit(self):
        self.min_spinbox.setValue(self.min_spinbox.value() *
                                  self.data_scaling / self.data_scaling_prev)
        self.max_spinbox.setValue(self.max_spinbox.value() *
                                  self.data_scaling / self.data_scaling_prev)

        self.min_spinbox.setSuffix(self.data_unit)
        self.max_spinbox.setSuffix(self.data_unit)

        self.data_scaling_prev = self.data_scaling


class HoverMixin():
    hovered = Signal(str)

    def __init__(self, view):
        self.view = view

    def hover_event(self, x, y, v):
        if x != -1 and y != -1:
            string = f'X: {(x-self.data_center_x)*self.axis_scaling:.{self.axis_precision}f}{self.axis_unit}, Y: {(y-self.data_center_y)*self.axis_scaling:.{self.axis_precision}f}{self.axis_unit}, V: {v:.{self.data_precision}f}{self.data_unit}'

            self.hovered.emit(string)
        else:
            self.hovered.emit('')
