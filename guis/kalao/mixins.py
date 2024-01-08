import numpy as np

from PySide6.QtCore import (QObject, QRunnable, QSignalBlocker, QThreadPool,
                            Signal, Slot)
from PySide6.QtGui import QCursor, QGuiApplication, QImage, Qt
from PySide6.QtWidgets import QCheckBox, QComboBox

from kalao.utils.image import LinearScale

from guis.kalao import colormaps
from guis.kalao.string_formatter import KalAOFormatter

import config


class ArrayToImageMixin:
    colormap = colormaps.BlackBody()
    image = None

    def __init__(self, *args, **kwargs):
        pass

    def prepare_array_for_qimage(self, img, img_min=None, img_max=None,
                                 scale=LinearScale):
        if len(img.shape) < 2:
            img = img[np.newaxis, :]

        if img_min is None:
            img_min = img.min()

        if img_max is None:
            img_max = img.max()

        delta = img_max - img_min

        scale_min = self.colormap.min
        scale_max = self.colormap.max

        if self.colormap.color_saturation_high is not None:
            scale_max -= 0.4999

        if self.colormap.color_saturation_low is not None:
            scale_min += 0.4999

        if np.ma.is_masked(img):
            mask = img.mask
            img = img.filled()
        else:
            mask = None

        if delta > config.epsilon:
            rescale = (scale_max-scale_min) / delta
            offset = img_min*rescale - scale_min

            img_scaled = img*rescale - offset
            img_scaled = np.clip(img_scaled, scale_min, scale_max)
            img_scaled = scale(scale_min, scale_max).scale(img_scaled)
            img_scaled = np.rint(img_scaled).astype(int)
        else:
            img_scaled = np.ones(img.shape) * self.colormap.no_data_value

        if mask is not None:
            if self.colormap.has_transparency:
                img_scaled[mask] = self.colormap.transparency_value
            else:
                img_scaled[mask] = self.colormap.no_data_value

        self.img_uint8 = np.require(img_scaled, np.uint8, 'C')
        self.image = QImage(self.img_uint8.data, self.img_uint8.shape[1],
                            self.img_uint8.shape[0], self.img_uint8.shape[1],
                            QImage.Format_Indexed8)
        self.image.setColorTable(self.colormap.colormap)


class MinMaxMixin:
    data_unit = ''
    data_scaling = 1
    data_precision = 0
    data_center_x = 0
    data_center_y = 0

    axis_unit = ''
    axis_scaling = 1
    axis_precision = 0

    autoscale_min = -np.inf
    autoscale_max = np.inf

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.views = []

    def init_minmax(self, view_list=[], symetric=False):
        self.min_spinbox.setMaximum(self.max_spinbox.value())
        self.max_spinbox.setMinimum(self.min_spinbox.value())
        self.min_spinbox.setReadOnly(self.autoscale_checkbox.isChecked())
        self.max_spinbox.setReadOnly(self.autoscale_checkbox.isChecked())

        if not isinstance(view_list, list):
            view_list = [view_list]

        self.views = view_list

        self.data_symetric = symetric

        self.update_spinboxes_unit(self.data_unit, self.data_scaling,
                                   self.data_precision)

    @Slot(float)
    def on_min_spinbox_valueChanged(self, d):
        self.max_spinbox.setMinimum(d)

        for view in self.views:
            view.updateMinMax(self.min_spinbox.value(),
                              self.max_spinbox.value())

    @Slot(float)
    def on_max_spinbox_valueChanged(self, d):
        self.min_spinbox.setMaximum(d)

        for view in self.views:
            view.updateMinMax(self.min_spinbox.value(),
                              self.max_spinbox.value())

    @Slot(int)
    def on_autoscale_checkbox_stateChanged(self, state):
        self.min_spinbox.setReadOnly(Qt.CheckState(state) == Qt.Checked)
        self.max_spinbox.setReadOnly(Qt.CheckState(state) == Qt.Checked)

        if self.autoscale_checkbox.isChecked() and not (np.isinf(
                self.autoscale_min) or np.isinf(self.autoscale_max)):
            with QSignalBlocker(self.min_spinbox):
                self.min_spinbox.setMaximum(self.autoscale_max)
                self.min_spinbox.setValue(self.autoscale_min)

            with QSignalBlocker(self.max_spinbox):
                self.max_spinbox.setMinimum(self.autoscale_min)
                self.max_spinbox.setValue(self.autoscale_max)

            for view in self.views:
                view.updateMinMax(self.autoscale_min, self.autoscale_max)

        # if self.autoscale_checkbox.isChecked():
        #     self.min_spinbox.setButtonSymbols(QAbstractSpinBox.NoButtons)
        #     self.max_spinbox.setButtonSymbols(QAbstractSpinBox.NoButtons)
        # else:
        #     self.min_spinbox.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        #     self.max_spinbox.setButtonSymbols(QAbstractSpinBox.UpDownArrows)

    @Slot(bool)
    def on_fullscale_button_clicked(self, checked):
        self.autoscale_checkbox.setChecked(False)

        with QSignalBlocker(self.min_spinbox):
            self.min_spinbox.setMaximum(self.stream_info['max'])
            self.min_spinbox.setValue(self.stream_info['min'])

        with QSignalBlocker(self.max_spinbox):
            self.max_spinbox.setMinimum(self.stream_info['min'])
            self.max_spinbox.setValue(self.stream_info['max'])

        for view in self.views:
            view.updateMinMax(self.stream_info['min'] * self.data_scaling,
                              self.stream_info['max'] * self.data_scaling)

    def update_spinboxes_unit(self, unit, scaling, precision):
        self.min_spinbox.setScale(scaling, precision)
        self.max_spinbox.setScale(scaling, precision)

        self.min_spinbox.setSuffix(unit)
        self.max_spinbox.setSuffix(unit)

        self.data_scaling = scaling
        self.data_unit = unit
        self.data_precision = precision

    def compute_min_max(self, img, cuts=None):
        if cuts is None:
            img_min = img.min()
            img_max = img.max()
        else:
            img_min, img_max = cuts.cut(img)

        if self.data_symetric:
            abs_max = max(abs(img_min), abs(img_max))
            img_min = -abs_max
            img_max = abs_max

        self.autoscale_min = img_min
        self.autoscale_max = img_max

        if self.autoscale_checkbox.isChecked():
            with QSignalBlocker(self.min_spinbox):
                self.min_spinbox.setMaximum(img_max)
                self.min_spinbox.setValue(img_min)

            with QSignalBlocker(self.max_spinbox):
                self.max_spinbox.setMinimum(img_min)
                self.max_spinbox.setValue(img_max)
        else:
            img_min = self.min_spinbox.value()
            img_max = self.max_spinbox.value()

        return img_min, img_max


class SceneHoverMixin:
    hovered = Signal(str)
    formatter = KalAOFormatter()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def hover_xyv_to_str(self, x, y, v):
        if x != -1 and y != -1:
            string = self.formatter.format(
                'X: {x:.{axis_precision}f}{axis_unit}, Y: {y:.{axis_precision}f}{axis_unit}, V: {v:.{data_precision}f}{data_unit}',
                x=(x - self.data_center_x) * self.axis_scaling,
                y=(y - self.data_center_y) * self.axis_scaling,
                v=v * self.data_scaling, axis_precision=self.axis_precision,
                axis_unit=self.axis_unit, data_precision=self.data_precision,
                data_unit=self.data_unit)

            self.hovered.emit(string)
        else:
            self.hovered.emit('')


class BackendWorker(QObject, QRunnable):
    done = Signal()

    def __init__(self, fun, *args, **kwargs):
        super().__init__()
        QRunnable.__init__(self)

        self.fun = fun
        self.args = args
        self.kwargs = kwargs

    def run(self):
        self.fun(*self.args, **self.kwargs)
        self.done.emit()


class BackendActionMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.threadpool = QThreadPool()

    def action_send(self, widget_list, fun, *args):
        QGuiApplication.setOverrideCursor(QCursor(Qt.BusyCursor))

        if not isinstance(widget_list, list):
            widget_list = [widget_list]

        if len(widget_list) > 0:
            widget_list[0].clearFocus()

        for widget in widget_list:
            widget.setEnabled(False)

        worker = BackendWorker(fun, *args)
        worker.done.connect(lambda: self.action_clean(widget_list))
        self.threadpool.start(worker)

    def action_clean(self, widget_list):
        QGuiApplication.restoreOverrideCursor()

        for widget in widget_list:
            widget.setEnabled(True)


class BackendDataMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.data_cache = {}

    def consume_metadata(self, data, key, default=None, force=False):
        try:
            return data['metadata'][key]
        except KeyError:
            return default

    def consume_stream(self, data, stream_name, default=None, force=False):
        try:
            if stream_name not in self.data_cache:
                self.data_cache[stream_name] = {}

            cnt0 = data[stream_name]['cnt0']
            prev = self.data_cache[stream_name].get('cnt0', None)

            if cnt0 != prev or force:
                self.data_cache[stream_name]['cnt0'] = cnt0
                return data[stream_name]['data']
            else:
                return default
        except KeyError:
            return default

    def consume_stream_keyword(self, data, stream_name, key, default=None,
                               force=False):
        try:
            if stream_name not in self.data_cache:
                self.data_cache[stream_name] = {}

            if 'keywords' not in self.data_cache[stream_name]:
                self.data_cache[stream_name]['keywords'] = {}

            value = data[stream_name]['keywords'][key]
            prev = self.data_cache[stream_name]['keywords'].get(key, None)

            if value != prev or force:
                self.data_cache[stream_name]['keywords'][key] = value
                return value
            else:
                return default
        except KeyError:
            return default

    def consume_stream_cnt(self, data, stream_name, default=None, force=False):
        try:
            if stream_name not in self.data_cache:
                self.data_cache[stream_name] = {}

            value = data[stream_name]['cnt0']
            prev = self.data_cache[stream_name].get('cnt0', None)

            if value != prev or force:
                return value
            else:
                return default
        except KeyError:
            return default

    def consume_param(self, data, fps_name, param_name, default=None,
                      force=False):
        try:
            if fps_name not in self.data_cache:
                self.data_cache[fps_name] = {}

            value = data[fps_name][param_name]
            prev = self.data_cache[fps_name].get(param_name, None)

            if value != prev or force:
                self.data_cache[fps_name][param_name] = value
                return value
            else:
                return default
        except KeyError:
            return default

    def consume_dict(self, data, key_dict, key, default=None, force=False):
        try:
            if key_dict not in self.data_cache:
                self.data_cache[key_dict] = {}

            value = data[key_dict][key]
            prev = self.data_cache[key_dict].get(key, None)

            if value != prev or force:
                self.data_cache[key_dict][key] = value
                return value
            else:
                return default
        except KeyError:
            return default

    def consume_db(self, data, collection, key, default=(None, None),
                   force=False):
        try:
            if collection not in self.data_cache:
                self.data_cache[collection] = {}

            value = data[collection][key][0]['value']
            timestamp = data[collection][key][0]['timestamp']

            prev = self.data_cache[collection].get(key, None)

            if timestamp != prev or force:
                self.data_cache[collection][key] = timestamp
                return value, timestamp
            else:
                return default
        except KeyError:
            return default

    def data_to_widget(self, data, widget, true_value=[]):
        if data is None:
            return

        with QSignalBlocker(widget):
            if isinstance(widget, QComboBox):
                if isinstance(data, int):
                    widget.setCurrentIndex(data)
                else:
                    widget.setCurrentIndex(widget.findData(data))
            elif isinstance(widget, QCheckBox):
                if not isinstance(true_value, list):
                    true_value = [true_value]

                widget.setChecked(data in true_value)
            else:
                widget.setValue(data)
