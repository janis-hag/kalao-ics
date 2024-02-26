import traceback
from pathlib import Path

import numpy as np

from PySide6.QtCore import (QEventLoop, QObject, QRunnable, QSignalBlocker,
                            QThreadPool, Signal, Slot)
from PySide6.QtGui import QCursor, QGuiApplication, Qt
from PySide6.QtWidgets import QCheckBox, QComboBox, QMessageBox

from kalao.utils.rprint import rprint

from guis.utils.string_formatter import KalAOFormatter
from guis.utils.widgets import KMessageBox


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
            self.min_spinbox.setMaximum(self.image_info['max'])
            self.min_spinbox.setValue(self.image_info['min'])

        with QSignalBlocker(self.max_spinbox):
            self.max_spinbox.setMinimum(self.image_info['min'])
            self.max_spinbox.setValue(self.image_info['max'])

        for view in self.views:
            view.updateMinMax(self.image_info['min'] * self.data_scaling,
                              self.image_info['max'] * self.data_scaling)

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
    exception = None
    ret = None

    def __init__(self, fun, **kwargs):
        super().__init__()
        QRunnable.__init__(self)

        self.fun = fun
        self.kwargs = kwargs

    def run(self):
        try:
            self.ret = self.fun(**self.kwargs)
        except Exception as e:
            rprint(''.join(traceback.format_exception(e)))
            self.exception = e

        self.done.emit()


class BackendActionMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.threadpool = QThreadPool()

    def action_send(self, widget_list, fun, **kwargs):
        QGuiApplication.setOverrideCursor(QCursor(Qt.BusyCursor))

        if not isinstance(widget_list, list):
            widget_list = [widget_list]

        if len(widget_list) > 0:
            widget_list[0].clearFocus()

        for widget in widget_list:
            widget.setEnabled(False)

        loop = QEventLoop()
        worker = BackendWorker(fun, **kwargs)
        worker.done.connect(loop.quit)

        self.threadpool.start(worker)
        loop.exec()

        QGuiApplication.restoreOverrideCursor()

        for widget in widget_list:
            widget.setEnabled(True)

        if worker.exception is not None:
            msgbox = KMessageBox(self)
            msgbox.setIcon(QMessageBox.Critical)
            msgbox.setText("<b>An error occured!</b>")
            msgbox.setInformativeText(
                f'An error occurred during action, please check the logs.')
            msgbox.setModal(True)
            msgbox.show()

        return worker.ret


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

    def consume_fits(self, data, fits_file, default=None, force=False):
        try:
            if not isinstance(fits_file, Path):
                fits_file = Path(fits_file)

            key = fits_file.stem

            if key not in self.data_cache:
                self.data_cache[key] = {}

            mtime = data[key]['mtime']
            prev = self.data_cache[key].get('mtime', None)

            if mtime != prev or force:
                self.data_cache[key]['mtime'] = mtime
                return data[key]['data']
            else:
                return default
        except KeyError:
            return default

    def consume_fits_full(self, data, fits_file, default=None, force=False):
        try:
            if not isinstance(fits_file, Path):
                fits_file = Path(fits_file)

            key = fits_file.stem

            if key not in self.data_cache:
                self.data_cache[key] = {}

            mtime = data[key]['mtime']
            prev = self.data_cache[key].get('mtime', None)

            if mtime != prev or force:
                self.data_cache[key]['mtime'] = mtime
                return data[key]['hdul']
            else:
                return default
        except KeyError:
            return default

    def consume_fits_mtime(self, data, fits_file, default=None, force=False):
        try:
            if not isinstance(fits_file, Path):
                fits_file = Path(fits_file)

            key = fits_file.stem

            if key not in self.data_cache:
                self.data_cache[key] = {}

            value = data[key]['mtime']
            prev = self.data_cache[key].get('mtime', None)

            if value != prev or force:
                return value
            else:
                return default
        except KeyError:
            return default

    def data_to_widget(self, data, widget, true_value=[True]):
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
