from PySide6.QtCore import Slot

from guis.kalao.ui_loader import loadUi
from guis.kalao.widgets import KalAOWidget
from guis.windows.dm_channels import DMChannelsWindow


class EngineeringWidget(KalAOWidget):
    def __init__(self, backends, backend, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.backends = backends
        self.backend = backend

        loadUi('engineering.ui', self)
        self.resize(600, 400)

    @Slot(bool)
    def on_dm_channels_button_clicked(self, checked):
        self.dm_channels = DMChannelsWindow(self.backends, 1)

    @Slot(bool)
    def on_ttm_channels_button_clicked(self, checked):
        self.ttm_channels = DMChannelsWindow(self.backends, 2)

    @Slot(bool)
    def on_dm_calibration_button_clicked(self, checked):
        from guis.windows.calibration import CalibrationWindow
        self.dm_calibration = CalibrationWindow('dm', 1, (11, 22), (12, 12))

    @Slot(bool)
    def on_ttm_calibration_button_clicked(self, checked):
        from guis.windows.calibration import CalibrationWindow
        self.ttm_calibration = CalibrationWindow('ttm', 2, (12, 12), (1, 2))