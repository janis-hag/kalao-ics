import numpy as np

from PySide6.QtCore import Signal, Slot
from PySide6.QtGui import QImage, Qt

from guis.kalao import colormaps


class ArrayToImageMixin():
    colormap = colormaps.BlackBody()
    image = None
    epsilon = 1e-12

    def prepare_array_for_qimage(self, img, img_min=None, img_max=None):
        if img_min is None:
            img_min = img.min()

        if img_max is None:
            img_max = img.max()

        delta = img_max - img_min

        scale_max = 255
        scale_min = 0

        if self.colormap.has_transparency:
            scale_max -= 1

        if self.colormap.color_saturation_high is not None:
            scale_max -= 0.51

        if self.colormap.color_saturation_low is not None:
            scale_min += 0.51

        if np.ma.is_masked(img):
            mask = img.mask
            img = img.filled()
        else:
            mask = None

        if delta > self.epsilon:
            rescale = (scale_max-scale_min) / delta
            offset = img_min*rescale - scale_min

            img_scaled = img*rescale - offset
            img_scaled = np.rint(img_scaled).astype(int)
            img_scaled = np.clip(img_scaled, 0, 255)
        else:
            img_scaled = np.ones(img.shape) * 128

        if mask is not None and self.colormap.has_transparency:
            img_scaled[mask] = 255

        self.img_uint8 = np.require(img_scaled, np.uint8, 'C')
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

    def init(self):
        self.on_autoscale_checkbox_stateChanged(
            self.autoscale_checkbox.checkState())
        self.on_min_spinbox_valueChanged(self.min_spinbox.value())
        self.on_max_spinbox_valueChanged(self.max_spinbox.value())
        self.update_spinboxes_unit()

    @Slot(float)
    def on_min_spinbox_valueChanged(self, d):
        self.data_min = d
        self.max_spinbox.setMinimum(d)

    @Slot(float)
    def on_max_spinbox_valueChanged(self, d):
        self.data_max = d
        self.min_spinbox.setMaximum(d)

        if not self.autoscale_checkbox.isChecked():
            print(f"New max: {d}")

    @Slot(int)
    def on_autoscale_checkbox_stateChanged(self, state):
        self.min_spinbox.setReadOnly(Qt.CheckState(state) == Qt.Checked)
        self.max_spinbox.setReadOnly(Qt.CheckState(state) == Qt.Checked)

    @Slot(bool)
    def on_fullscale_button_clicked(self, checked):
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

    def compute_min_max(self, img, symetric=False):
        if self.autoscale_checkbox.isChecked():
            img_min = img.min()
            img_max = img.max()

            if symetric:
                abs_max = max(abs(img_min), abs(img_max))
                img_min = -abs_max
                img_max = abs_max

            self.min_spinbox.setValue(img_min * self.data_scaling)
            self.max_spinbox.setValue(img_max * self.data_scaling)
        else:
            img_min = self.data_min / self.data_scaling
            img_max = self.data_max / self.data_scaling

        return img_min, img_max


class HoverMixin():
    hovered = Signal(str)

    def hover_event(self, x, y, v):
        if x != -1 and y != -1:
            string = f'X: {(x-self.data_center_x)*self.axis_scaling:.{self.axis_precision}f}{self.axis_unit}, Y: {(y-self.data_center_y)*self.axis_scaling:.{self.axis_precision}f}{self.axis_unit}, V: {v*self.data_scaling:.{self.data_precision}f}{self.data_unit}'

            self.hovered.emit(string)
        else:
            self.hovered.emit('')
