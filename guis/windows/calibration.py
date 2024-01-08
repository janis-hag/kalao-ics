import numpy as np

from PySide6.QtCore import Slot
from PySide6.QtGui import QCursor, QGuiApplication, Qt

from guis.kalao.mixins import SceneHoverMixin
from guis.kalao.ui_loader import loadUi
from guis.kalao.widgets import KGraphicsView, KMainWindow


class CalibrationWindow(KMainWindow, SceneHoverMixin):
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

        for key in dir(self):
            attr = getattr(self, key)

            if isinstance(attr, KGraphicsView):
                attr.hovered.connect(self.hover_xyv_to_str)

        self.hovered.connect(self.info_to_statusbar)

        self.on_reload_button_clicked(False)
        self.on_mode_spinbox_valueChanged(self.mode_spinbox.value())

        self.center()
        self.show()

    def max_mode_number(self):
        s = np.inf

        data = self.data.get('CMmodesDM', {}).get('data')
        if data is not None:
            s = min(s, data.shape[0])

        data = self.data.get('CMmodesWFS', {}).get('data')
        if data is not None:
            s = min(s, data.shape[0])

        data = self.data.get(f'aol{self.loop}_DMmodes', {}).get('data')
        if data is not None:
            s = min(s, data.shape[2])

        data = self.data.get(f'aol{self.loop}_modesWFS', {}).get('data')
        if data is not None:
            s = min(s, data.shape[2])

        if np.isinf(s):
            return 0
        else:
            return s - 1

    @Slot(bool)
    def on_reload_button_clicked(self, checked):
        QGuiApplication.setOverrideCursor(QCursor(Qt.BusyCursor))

        self.data = self.backend.get_calibration_data(self.conf, self.loop)

        QGuiApplication.restoreOverrideCursor()

        self.mode_spinbox.setMaximum(self.max_mode_number())

    @Slot(int)
    def on_mode_spinbox_valueChanged(self, i):
        self.update_image_fits('wfsref', 'wfsref')
        self.update_image_fits('wfsrefc', 'wfsrefc')
        self.update_image_fits('wfsmask', 'wfsmask')
        self.update_image_fits('wfsmap', 'wfsmap')
        self.update_image_fits('dmmask', 'dmmask')
        self.update_image_fits('dmmap', 'dmmap')
        self.update_image_fits('DMmodes', 'CMmodesDM')
        self.update_image_fits('modesWFS', 'CMmodesWFS')

        self.update_image_stream('wfsref', f'aol{self.loop}_wfsref')
        self.update_image_stream('wfsrefc', f'aol{self.loop}_wfsrefc')
        self.update_image_stream('wfsmask', f'aol{self.loop}_wfsmask')
        self.update_image_stream('wfsmap', f'aol{self.loop}_wfsmap')
        self.update_image_stream('dmmask', f'aol{self.loop}_dmmask')
        self.update_image_stream('dmmap', f'aol{self.loop}_dmmap')
        self.update_image_stream('DMmodes', f'aol{self.loop}_DMmodes')
        self.update_image_stream('modesWFS', f'aol{self.loop}_modesWFS')

    def update_image_fits(self, view_key, data_key):
        view = getattr(self, f'{view_key}_fits_view')
        data = self.data.get(data_key, {}).get('data')

        if data is not None:
            if len(data.shape) == 2:
                view.setImage(data)
            else:
                view.setImage(data[self.mode_spinbox.value(), :, :])

    def update_image_stream(self, view_key, data_key):
        view = getattr(self, f'{view_key}_stream_view')
        data = self.data.get(data_key, {}).get('data')

        if data is not None:
            if len(data.shape) == 2:
                view.setImage(data)
            else:
                view.setImage(data[:, :, self.mode_spinbox.value()])
