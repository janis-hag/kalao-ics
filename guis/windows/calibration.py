import numpy as np

from PySide6.QtCharts import QScatterSeries, QValueAxis
from PySide6.QtCore import QPointF, Slot
from PySide6.QtGui import QBrush, QCursor, QGuiApplication, QPen, Qt

from guis.utils.definitions import Color
from guis.utils.mixins import BackendDataMixin, SceneHoverMixin
from guis.utils.ui_loader import loadUi
from guis.utils.widgets import KGraphicsView, KMainWindow


class CalibrationWindow(KMainWindow, SceneHoverMixin, BackendDataMixin):
    data_unit = ''
    data_scaling = 1
    data_precision = 0
    data_center_x = 0
    data_center_y = 0

    axis_unit = ''
    axis_scaling = 1
    axis_precision = 0

    def __init__(self, backend, conf, loop, wfs_shape, dm_shape, parent=None):
        super().__init__(parent)

        self.backend = backend
        self.data = {}

        self.conf = conf
        self.loop = loop
        self.wfs_shape = wfs_shape
        self.dm_shape = dm_shape

        loadUi('calibration.ui', self)
        self.resize(800, 400)

        self.setWindowTitle(f'{conf.upper()} - {self.windowTitle()}')

        ### Calibration tab

        for key in dir(self):
            attr = getattr(self, key)

            if isinstance(attr, KGraphicsView):
                attr.hovered.connect(self.hover_xyv_to_str)

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
        s = np.inf

        data = self.data.get('CMmodesDM', {}).get('data')
        if data is not None:
            s = min(s, data.shape[0])

        data = self.data.get('CMmodesWFS', {}).get('data')
        if data is not None:
            s = min(s, data.shape[0])

        data = self.data.get(f'aol{self.loop}_DMmodes', {}).get('data')
        if data is not None:
            s = min(s, data.shape[len(data.shape) - 1])

        data = self.data.get(f'aol{self.loop}_modesWFS', {}).get('data')
        if data is not None:
            s = min(s, data.shape[len(data.shape) - 1])

        if np.isinf(s):
            return 1
        else:
            return s

    @Slot(bool)
    def on_refresh_button_clicked(self, checked):
        QGuiApplication.setOverrideCursor(QCursor(Qt.BusyCursor))

        self.data = self.backend.get_calibration_data(self.conf, self.loop)

        QGuiApplication.restoreOverrideCursor()

        modes = self.number_of_modes()
        self.mode_spinbox.setMaximum(modes - 1)
        self.mode_spinbox.setSuffix(f' / {modes}')

        self.on_mode_spinbox_valueChanged(self.mode_spinbox.value())

    @Slot(int)
    def on_mode_spinbox_valueChanged(self, i):
        self.update_image_fits('wfsref', 'wfsref')
        self.update_image_fits('wfsrefc', 'wfsrefc')
        self.update_image_fits('wfsmask', 'wfsmask')
        self.update_image_fits('wfsmap', 'wfsmap')
        self.update_image_fits('dmmask', 'dmmask')
        self.update_image_fits('dmmap', 'dmmap')
        self.update_image_fits('DMmodes', 'CMmodesDM', cube=True)
        self.update_image_fits('modesWFS', 'CMmodesWFS', cube=True)

        self.update_image_stream('wfsref', f'aol{self.loop}_wfsref')
        self.update_image_stream('wfsrefc', f'aol{self.loop}_wfsrefc')
        self.update_image_stream('wfsmask', f'aol{self.loop}_wfsmask')
        self.update_image_stream('wfsmap', f'aol{self.loop}_wfsmap')
        self.update_image_stream('dmmask', f'aol{self.loop}_dmmask')
        self.update_image_stream('dmmap', f'aol{self.loop}_dmmap')
        self.update_image_stream('DMmodes', f'aol{self.loop}_DMmodes',
                                 cube=True)
        self.update_image_stream('modesWFS', f'aol{self.loop}_modesWFS',
                                 cube=True)

    def update_image_fits(self, view_key, data_key, cube=False):
        view = getattr(self, f'{view_key}_fits_view')
        data = self.data.get(data_key, {}).get('data')

        if data is not None:
            if not cube:
                view.setImage(data)
            elif len(data.shape) == 2:
                view.setImage(data[self.mode_spinbox.value(), :])
            elif len(data.shape) == 3:
                view.setImage(data[self.mode_spinbox.value(), :, :])
            else:
                raise Exception(
                    f'Unexpected image size {len(data.shape)} for {data_key}')

    def update_image_stream(self, view_key, data_key, cube=False):
        view = getattr(self, f'{view_key}_stream_view')
        data = self.data.get(data_key, {}).get('data')

        if not cube:
            view.setImage(data)
        elif len(data.shape) == 2:
            view.setImage(data[:, self.mode_spinbox.value()])
        elif len(data.shape) == 3:
            view.setImage(data[:, :, self.mode_spinbox.value()])
        else:
            raise Exception(
                f'Unexpected image size {len(data.shape)} for {data_key}')

    @Slot(bool)
    def on_reload_button_clicked(self, checked):
        QGuiApplication.setOverrideCursor(QCursor(Qt.BusyCursor))

        self.data = self.backend.get_calibration_reload()

        QGuiApplication.restoreOverrideCursor()

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

        data = self.backend.get_latency_measure(self.conf, self.loop)

        QGuiApplication.restoreOverrideCursor()

        # Display data

        framerateHz = self.consume_param(data, f'mlat-{self.loop}',
                                         'out.framerateHz')
        if framerateHz is not None:
            self.latency_framerate_lineedit.setText(f'{framerateHz:.2f} Hz')

        latencyfr = self.consume_param(data, f'mlat-{self.loop}',
                                       'out.latencyfr')
        if latencyfr is not None:
            self.latency_frames_lineedit.setText(f'{latencyfr:.2f} frames')

        # TODO: error if all nan

        for i in range(data['hardwlatencypts'].shape[0]):
            self.latency_series.append(
                QPointF(data['hardwlatencypts'][i, 1] * 1000,
                        data['hardwlatencypts'][i, 2]))

        self.latency_axis_y.setRange(
            0, data['hardwlatencypts'][:, 2].max() * 1.05)
