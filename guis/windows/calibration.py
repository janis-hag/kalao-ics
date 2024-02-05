import numpy as np

from PySide6.QtCharts import QScatterSeries, QValueAxis
from PySide6.QtCore import QPointF, Slot
from PySide6.QtGui import QBrush, QCursor, QGuiApplication, QPen, Qt
from PySide6.QtWidgets import QMessageBox

from guis.utils import colormaps
from guis.utils.definitions import Color
from guis.utils.mixins import BackendDataMixin, SceneHoverMixin
from guis.utils.ui_loader import loadUi
from guis.utils.widgets import KGraphicsView, KMainWindow, KMessageBox


class CalibrationWindow(KMainWindow, SceneHoverMixin, BackendDataMixin):
    data_unit = ''
    data_scaling = 1
    data_precision = 2
    data_center_x = 0
    data_center_y = 0

    axis_unit = ''
    axis_scaling = 1
    axis_precision = 0

    def __init__(self, backend, conf, loop, wfs_shape, dm_shape, parent=None):
        super().__init__(parent)

        self.backend = backend
        self.modes_data = {}

        self.conf = conf
        self.loop = loop
        self.wfs_shape = wfs_shape
        self.dm_shape = dm_shape

        loadUi('calibration.ui', self)
        self.resize(800, 400)

        self.setWindowTitle(f'{conf.upper()} - {self.windowTitle()}')

        ### Calibration tab

        self.calib_combobox.addItem('Loaded')
        self.calib_combobox.addItem('Configuration')

        for key in dir(self):
            attr = getattr(self, key)

            if isinstance(attr, KGraphicsView):
                attr.hovered.connect(self.hover_xyv_to_str)

                if key.startswith('modesWFS') or key.startswith(
                        'DMmodes') or key.startswith(
                            'wfsref') or key.startswith('wfsrefc'):
                    attr.updateColormap(colormaps.CoolWarm())

        self.hovered.connect(self.info_to_statusbar)

        self.on_refresh_button_clicked(False)

        ### Latency tab

        # Create Chart and set General Chart setting
        chart = self.latency_plot.chart()

        # Serie
        pen = QPen(Color.TRANSPARENT, 0, Qt.SolidLine, Qt.SquareCap,
                   Qt.MiterJoin)
        brush = QBrush(Color.BLUE, Qt.SolidPattern)

        series = self.latency_series = QScatterSeries()
        series.setPen(pen)
        series.setBrush(brush)
        series.setMarkerSize(3)
        series.setName("Latency")
        series.setPointsVisible(True)
        chart.addSeries(series)

        # X Axis Settings
        axis_x = self.latency_axis_x = QValueAxis()
        axis_x.setTickCount(7)
        axis_x.setRange(-1, 5)
        axis_x.setTitleText('Latency [ms]')
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)

        # Y Axis Settings
        axis_y = self.latency_axis_y = QValueAxis()
        axis_y.setTickCount(5)
        axis_y.setRange(0, 1)
        axis_y.setTitleText('Signal [a.u.]')
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)

        chart.legend().hide()

        self.clear_latency()

        ### Common

        self.center()
        self.show()

    ##### Calibration tab

    def number_of_modes(self):
        self.modes_number = np.inf
        self.modes_dm_min = np.inf
        self.modes_dm_max = -np.inf
        self.modes_wfs_min = np.inf
        self.modes_wfs_max = -np.inf

        if self.calib_combobox.currentText() == 'Configuration':
            data = self.modes_data.get('CMmodesDM', {}).get('data')
            if data is not None:
                self.modes_number = min(self.modes_number, data.shape[0])
                self.modes_min = min(self.modes_dm_min, data.min())
                self.modes_max = min(self.modes_dm_max, data.max())

            data = self.modes_data.get('CMmodesWFS', {}).get('data')
            if data is not None:
                self.modes_number = min(self.modes_number, data.shape[0])
                self.modes_min = min(self.modes_wfs_min, data.min())
                self.modes_max = min(self.modes_wfs_max, data.max())
        else:
            data = self.modes_data.get(f'aol{self.loop}_DMmodes',
                                       {}).get('data')
            if data is not None:
                self.modes_number = min(self.modes_number,
                                        data.shape[len(data.shape) - 1])
                self.modes_min = min(self.modes_dm_min, data.min())
                self.modes_max = min(self.modes_dm_max, data.max())

            data = self.modes_data.get(f'aol{self.loop}_modesWFS',
                                       {}).get('data')
            if data is not None:
                self.modes_number = min(self.modes_number,
                                        data.shape[len(data.shape) - 1])
                self.modes_min = min(self.modes_wfs_min, data.min())
                self.modes_max = min(self.modes_wfs_max, data.max())

        if np.isinf(self.modes_number):
            self.modes_number = 1

    @Slot(bool)
    def on_refresh_button_clicked(self, checked):
        QGuiApplication.setOverrideCursor(QCursor(Qt.BusyCursor))
        self.refresh_button.setEnabled(False)

        self.modes_data = self.backend.get_calibration_data(
            self.conf, self.loop)

        self.refresh_button.setEnabled(True)
        QGuiApplication.restoreOverrideCursor()

        self.number_of_modes()
        self.mode_spinbox.setMaximum(self.modes_number)
        self.mode_spinbox.setSuffix(f' / {self.modes_number}')

        self.update_calib_images()

    @Slot(int)
    def on_minmax_checkbox_valueChanged(self, i):
        self.number_of_modes()
        self.mode_spinbox.setMaximum(self.modes_number)
        self.mode_spinbox.setSuffix(f' / {self.modes_number}')

        self.update_calib_images()

    @Slot(int)
    def on_calib_combobox_currentIndexChanged(self, index):
        self.number_of_modes()
        self.mode_spinbox.setMaximum(self.modes_number)
        self.mode_spinbox.setSuffix(f' / {self.modes_number}')

        self.update_calib_images()

    @Slot(int)
    def on_mode_spinbox_valueChanged(self, i):
        self.update_calib_images()

    def update_calib_images(self):
        if self.calib_combobox.currentText() == 'Configuration':
            self.update_image_fits('wfsref', 'wfsref', symetric=True)
            self.update_image_fits('wfsrefc', 'wfsrefc', symetric=True)
            self.update_image_fits('wfsmask', 'wfsmask')
            self.update_image_fits('wfsmap', 'wfsmap')
            self.update_image_fits('dmmask', 'dmmask')
            self.update_image_fits('dmmap', 'dmmap')
            self.update_image_fits('DMmodes', 'CMmodesDM', cube=True,
                                   symetric=True)
            self.update_image_fits('modesWFS', 'CMmodesWFS', cube=True,
                                   symetric=True)
        else:
            self.update_image_stream('wfsref', f'aol{self.loop}_wfsref',
                                     symetric=True)
            self.update_image_stream('wfsrefc', f'aol{self.loop}_wfsrefc',
                                     symetric=True)
            self.update_image_stream('wfsmask', f'aol{self.loop}_wfsmask')
            self.update_image_stream('wfsmap', f'aol{self.loop}_wfsmap')
            self.update_image_stream('dmmask', f'aol{self.loop}_dmmask')
            self.update_image_stream('dmmap', f'aol{self.loop}_dmmap')
            self.update_image_stream('DMmodes', f'aol{self.loop}_DMmodes',
                                     cube=True, symetric=True)
            self.update_image_stream('modesWFS', f'aol{self.loop}_modesWFS',
                                     cube=True, symetric=True)

    def update_image_fits(self, view_key, data_key, cube=False,
                          symetric=False):
        view = getattr(self, f'{view_key}_view')
        data = self.modes_data.get(data_key, {}).get('data')

        if data is not None:
            if not cube:
                img = data
            elif len(data.shape) == 2:
                img = data[self.mode_spinbox.value() - 1, :]
            elif len(data.shape) == 3:
                img = data[self.mode_spinbox.value() - 1, :, :]
            else:
                raise Exception(
                    f'Unexpected image size {len(data.shape)} for {data_key}')

            img_min, img_max = self.compute_minmax(img, view_key, symetric)
            view.setImage(img, img_min, img_max)
        else:
            view.setImage(None)

    def update_image_stream(self, view_key, data_key, cube=False,
                            symetric=False):
        view = getattr(self, f'{view_key}_view')
        data = self.modes_data.get(data_key, {}).get('data')

        if data is not None:
            if not cube:
                img = data
            elif len(data.shape) == 2:
                # Note: mode axis is odd compared to 3D case, but is correct
                img = data[self.mode_spinbox.value() - 1, :]
            elif len(data.shape) == 3:
                img = data[:, :, self.mode_spinbox.value() - 1]
            else:
                raise Exception(
                    f'Unexpected image size {len(data.shape)} for {data_key}')

            img_min, img_max = self.compute_minmax(img, view_key, symetric)
            view.setImage(img, img_min, img_max)
        else:
            view.setImage(None)

    def compute_minmax(self, img, view_key, symetric):
        if self.minmax_checkbox.isEnabled():
            img_min = img.min()
            img_max = img.max()
        else:
            if view_key == 'DMmodes':
                img_min = self.modes_dm_min
                img_max = self.modes_dm_max
            else:
                img_min = self.modes_wfs_min
                img_max = self.modes_wfs_max

        if symetric:
            abs_max = max(abs(img_min), abs(img_max))
            img_min = -abs_max
            img_max = abs_max
        else:
            img_min = 0

        return img_min, img_max

    @Slot(bool)
    def on_reload_button_clicked(self, checked):
        QGuiApplication.setOverrideCursor(QCursor(Qt.BusyCursor))
        self.reload_button.setEnabled(False)

        data = self.backend.get_calibration_reload()

        self.reload_button.setEnabled(True)
        QGuiApplication.restoreOverrideCursor()

        self.check_subprocess_error(data)

        self.on_refresh_button_clicked(False)

    ##### Latency tab

    def clear_latency(self):
        self.latency_framerate_lineedit.setText(f'-- Hz')
        self.latency_frames_lineedit.setText(f'-- frames')

        self.latency_series.clear()

        self.latency_axis_y.setRange(0, 1)

    @Slot(bool)
    def on_latency_measure_button_clicked(self, checked):
        # Clear data

        self.clear_latency()

        # Take measurement

        QGuiApplication.setOverrideCursor(QCursor(Qt.BusyCursor))
        self.latency_measure_button.setEnabled(False)

        data = self.backend.get_latency_measure(self.conf, self.loop)

        self.latency_measure_button.setEnabled(True)
        QGuiApplication.restoreOverrideCursor()

        # Display data

        if self.check_subprocess_error(data):
            return

        framerateHz = self.consume_param(data, f'mlat-{self.loop}',
                                         'out.framerateHz')
        if framerateHz is not None:
            self.latency_framerate_lineedit.setText(f'{framerateHz:.2f} Hz')

        latencyfr = self.consume_param(data, f'mlat-{self.loop}',
                                       'out.latencyfr')
        if latencyfr is not None:
            self.latency_frames_lineedit.setText(f'{latencyfr:.2f} frames')

        latency_data = data.get('hardwlatencypts')
        if latency_data is not None:
            if np.isnan(latency_data[:, 2]).all():
                msgbox = KMessageBox(self)
                msgbox.setIcon(QMessageBox.Critical)
                msgbox.setText("<b>Latency measruement failed!</b>")
                msgbox.setInformativeText(
                    f'Even though the latency measurement succeeded, it only returned NaNs.'
                )
                msgbox.setModal(True)
                msgbox.show()
                return

            for i in range(latency_data.shape[0]):
                self.latency_series.append(
                    QPointF(latency_data[i, 1] * 1000, latency_data[i, 2]))

            self.latency_axis_y.setRange(0, latency_data[:, 2].max() * 1.05)

    def check_subprocess_error(self, data):
        if data['returncode'] == 0:
            return False

        msgbox = KMessageBox(self)
        msgbox.setIcon(QMessageBox.Critical)
        msgbox.setText("<b>An error occured!</b>")
        msgbox.setInformativeText(
            'The underlying cacao process failed. See below for more details.')
        msgbox.setDetailedText(data['stdout'])
        msgbox.setModal(True)
        msgbox.show()

        return True
