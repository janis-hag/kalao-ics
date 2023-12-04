import numpy as np

from PySide6.QtCore import Slot

from guis.kalao.ui_loader import loadUi
from guis.kalao.widgets import KalAOWidget
from guis.windows.dm_channels import DMChannelsWindow

from kalao.definitions.enums import FlipMirrorPosition, ShutterState

import config


class EngineeringWidget(KalAOWidget):
    def __init__(self, backend, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.backend = backend

        loadUi('engineering.ui', self)
        self.resize(600, 400)

        for state in ShutterState:
            if state != ShutterState.ERROR:
                self.shutter_combobox.addItem(state)

        for position in FlipMirrorPosition:
            if position != FlipMirrorPosition.ERROR:
                self.flipmirror_combobox.addItem(position)

        for filter in config.FilterWheel.position_list:
            self.filterwheel_combobox.addItem(self.filter_display_name(filter),
                                              filter)

    def filter_display_name(self, filter):
        name = config.FilterWheel.filter_infos[filter]['name']
        start = config.FilterWheel.filter_infos[filter]['start']
        end = config.FilterWheel.filter_infos[filter]['end']

        if np.isinf(start):
            start = '-∞'
        else:
            start = f'{start*1e9:.0f} nm'

        if np.isinf(end):
            end = '∞'
        else:
            end = f'{end*1e9:.0f} nm'

        return f'{name} ({start} – {end})'

    @Slot(bool)
    def on_dm_channels_button_clicked(self, checked):
        self.dm_channels = DMChannelsWindow(self.backend, 1)

    @Slot(bool)
    def on_ttm_channels_button_clicked(self, checked):
        self.ttm_channels = DMChannelsWindow(self.backend, 2)

    @Slot(bool)
    def on_dm_calibration_button_clicked(self, checked):
        from guis.windows.calibration import CalibrationWindow
        self.dm_calibration = CalibrationWindow('dm', 1, (11, 22), (12, 12))

    @Slot(bool)
    def on_ttm_calibration_button_clicked(self, checked):
        from guis.windows.calibration import CalibrationWindow
        self.ttm_calibration = CalibrationWindow('ttm', 2, (12, 12), (1, 2))
