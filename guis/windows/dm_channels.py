import functools

from PySide2.QtCore import QTimer

from guis.backends.simulation import DMChannelsBackend
from guis.kalao import colormaps
from guis.kalao.mixins import MinMaxMixin
from guis.kalao.ui_loader import loadUi
from guis.kalao.widgets import KalAOMainWindow

import config


class DMChannelsWindow(KalAOMainWindow, MinMaxMixin):
    associated_stream = config.Streams.DM
    stream_info = config.StreamInfo.dm01disp
    data_unit = ' um'
    data_precision = 3

    axis_unit = ' px'
    axis_precision = 0

    def __init__(self, dm_number, parent=None):
        super().__init__(parent)

        self.dm_number = dm_number

        if dm_number == 2:
            self.associated_stream = config.Streams.TTM
            self.stream_info = config.StreamInfo.dm02disp
            self.data_unit = ' mrad'
            self.data_precision = 2

        self.backend = DMChannelsBackend(dm_number)

        loadUi('dm_channels.ui', self)
        self.resize(400, 800)

        MinMaxMixin.__init__(self)

        self.timer = QTimer()
        self.timer.setInterval(int(1000. / config.GUI.max_fps))
        self.timer.timeout.connect(self.backend.update)
        self.timer.start()

        self.dm_view.setColormap(colormaps.CoolWarm())
        for i in range(0, 12):
            view = getattr(self, f'view_{i:02d}')
            view.setColormap(colormaps.CoolWarm())

            reset_button = getattr(self, f'reset_button_{i:02d}')
            partial = functools.partial(self.reset_channel, i)
            reset_button.clicked.connect(partial)

        self.reset_all_button.clicked.connect(self.reset_all_channel)

        self.backend.updated.connect(self.data_updated)

        self.show()

    def data_updated(self):
        if self.autoscale_checkbox.isChecked():
            img_min = self.backend.data[f'dm{self.dm_number:02d}disp'][
                'stream'].min()
            img_max = self.backend.data[f'dm{self.dm_number:02d}disp'][
                'stream'].max()

            abs_max = max(abs(img_min), abs(img_max))
            img_min = -abs_max
            img_max = abs_max

            self.min_spinbox.setValue(img_min)
            self.max_spinbox.setValue(img_max)
        else:
            img_min = self.data_min
            img_max = self.data_max

        self.dm_view.setImage(
            self.backend.data[f'dm{self.dm_number:02d}disp']['stream'],
            img_min, img_max)

        for i in range(0, 12):
            channel = f'dm{self.dm_number:02d}disp{i:02d}'

            view = getattr(self, f'view_{i:02d}')
            view.setImage(self.backend.data[channel]['stream'], img_min,
                          img_max)

    def reset_channel(self, i):
        self.backend.reset_channel(self.dm_number, i)

    def reset_all_channel(self, checked):
        self.backend.reset_dm(self.dm_number)

    def closeEvent(self, event):
        self.timer.stop()
        event.accept()
