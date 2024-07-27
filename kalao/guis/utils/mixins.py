import traceback
from pathlib import Path

import numpy as np

from PySide6.QtCore import (QEventLoop, QObject, QRunnable, QSignalBlocker,
                            QThreadPool, Signal, Slot)
from PySide6.QtGui import QCursor, QGuiApplication, Qt
from PySide6.QtWidgets import QCheckBox, QComboBox, QMessageBox

from kalao.utils.rprint import rprint

from kalao.guis.utils.string_formatter import KalAOFormatter
from kalao.guis.utils.widgets import KMessageBox


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
        # self.min_spinbox.setReadOnly(self.autoscale_button.isChecked())
        # self.max_spinbox.setReadOnly(self.autoscale_button.isChecked())

        if not isinstance(view_list, list):
            view_list = [view_list]

        self.views = view_list

        self.data_symetric = symetric

        self.update_spinboxes_unit(self.data_unit, self.data_scaling,
                                   self.data_precision)

    @Slot(float)
    def on_min_spinbox_valueChanged(self, d):
        self.autoscale_button.setChecked(False)
        self.fullscale_button.setChecked(False)

        self.max_spinbox.setMinimum(d)

        for view in self.views:
            view.updateMinMax(self.min_spinbox.value(),
                              self.max_spinbox.value())

    @Slot(float)
    def on_max_spinbox_valueChanged(self, d):
        self.autoscale_button.setChecked(False)
        self.fullscale_button.setChecked(False)

        self.min_spinbox.setMaximum(d)

        for view in self.views:
            view.updateMinMax(self.min_spinbox.value(),
                              self.max_spinbox.value())

    @Slot(bool)
    def on_autoscale_button_toggled(self, checked):
        # self.min_spinbox.setReadOnly(checked)
        # self.max_spinbox.setReadOnly(checked)

        if checked:
            self.fullscale_button.setChecked(False)

            if not np.isinf(self.autoscale_min) and not np.isinf(
                    self.autoscale_max):
                with QSignalBlocker(self.min_spinbox):
                    self.min_spinbox.setMaximum(self.autoscale_max)
                    self.min_spinbox.setValue(self.autoscale_min)

                with QSignalBlocker(self.max_spinbox):
                    self.max_spinbox.setMinimum(self.autoscale_min)
                    self.max_spinbox.setValue(self.autoscale_max)

                for view in self.views:
                    view.updateMinMax(self.autoscale_min, self.autoscale_max)

        #     self.min_spinbox.setButtonSymbols(QAbstractSpinBox.NoButtons)
        #     self.max_spinbox.setButtonSymbols(QAbstractSpinBox.NoButtons)
        # else:
        #     self.min_spinbox.setButtonSymbols(QAbstractSpinBox.UpDownArrows)
        #     self.max_spinbox.setButtonSymbols(QAbstractSpinBox.UpDownArrows)

    @Slot(bool)
    def on_fullscale_button_toggled(self, checked):
        if checked:
            self.autoscale_button.setChecked(False)

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

        if self.autoscale_button.isChecked():
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
        if not np.isnan(x) and not np.isnan(y):
            x = int(x)
            y = int(y)

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

        for widget in widget_list:
            widget.clearFocus()
            widget.setEnabledStack(False, f'action_{fun.__name__}')

        loop = QEventLoop()
        worker = BackendWorker(fun, **kwargs)
        worker.done.connect(loop.quit)

        self.threadpool.start(worker)
        loop.exec()

        QGuiApplication.restoreOverrideCursor()

        for widget in widget_list:
            widget.setEnabledStack(True, f'action_{fun.__name__}')

        if worker.exception is not None:
            msgbox = KMessageBox(self)
            msgbox.setIcon(QMessageBox.Critical)
            msgbox.setText('<b>An error occured!</b>')
            msgbox.setInformativeText(
                f'An error occurred during call to "{fun.__name__}".')
            msgbox.setDetailedText(''.join(
                traceback.format_exception(worker.exception)))
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

    def consume_shm(self, data, shm_name, default=None, force=False):
        try:
            if shm_name not in self.data_cache:
                self.data_cache[shm_name] = {}

            cnt0 = data[shm_name]['cnt0']
            prev = self.data_cache[shm_name].get('cnt0', None)

            if cnt0 != prev or force:
                self.data_cache[shm_name]['cnt0'] = cnt0
                return data[shm_name]['data']
            else:
                return default
        except KeyError:
            return default

    def consume_shm_keyword(self, data, shm_name, key, default=None,
                            force=False):
        try:
            if shm_name not in self.data_cache:
                self.data_cache[shm_name] = {}

            if 'keywords' not in self.data_cache[shm_name]:
                self.data_cache[shm_name]['keywords'] = {}

            value = data[shm_name]['keywords'][key]
            prev = self.data_cache[shm_name]['keywords'].get(key, None)

            if value != prev or force:
                self.data_cache[shm_name]['keywords'][key] = value
                return value
            else:
                return default
        except KeyError:
            return default

    def consume_shm_status(self, data, shm_name, default=None, force=False):
        try:
            if shm_name not in self.data_cache:
                self.data_cache[shm_name] = {}

            value = data[shm_name]['status']
            prev = self.data_cache[shm_name].get('status', None)

            if value != prev or force:
                self.data_cache[shm_name]['status'] = value
                return value
            else:
                return default
        except KeyError:
            return default

    def consume_shm_md(self, data, shm_name, default=None, force=False):
        try:
            if shm_name not in self.data_cache:
                self.data_cache[shm_name] = {}

            value = data[shm_name]['md']
            prev = self.data_cache[shm_name].get('md', None)

            if value != prev or force:
                self.data_cache[shm_name]['md'] = value
                return value
            else:
                return default
        except KeyError:
            return default

    def consume_fps_param(self, data, fps_name, param_name, default=None,
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

    def consume_fps_status(self, data, fps_name, default=None, force=False):
        try:
            if fps_name not in self.data_cache:
                self.data_cache[fps_name] = {}

            value = data[fps_name]['status']
            prev = self.data_cache[fps_name].get('status', None)

            if value != prev or force:
                self.data_cache[fps_name]['status'] = value
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

            value = data[collection][key]['value']
            timestamp = data[collection][key]['timestamp']

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
