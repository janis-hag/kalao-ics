import functools

from PySide6.QtCore import QTimer, Slot

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

    def __init__(self, backends, dm_number, parent=None):
        super().__init__(parent)

        self.dm_number = dm_number

        if dm_number == 2:
            self.associated_stream = config.Streams.TTM
            self.stream_info = config.StreamInfo.dm02disp
            self.data_unit = ' mrad'
            self.data_precision = 2

        self.backend = backends.DMChannelsBackend(dm_number)

        loadUi('dm_channels.ui', self)
        self.resize(400, 800)

        MinMaxMixin.init(self)

        self.timer = QTimer()
        self.timer.setInterval(int(1000. / config.GUI.max_fps))
        self.timer.timeout.connect(self.backend.update)
        self.timer.start()

        self.dm_view.setColormap(colormaps.CoolWarm())
        for i in range(0, 12):
            view = getattr(self, f'view_{i:02d}')
            view.setColormap(colormaps.CoolWarm())

            reset_button = getattr(self, f'reset_button_{i:02d}')
            reset_button.clicked.connect(lambda checked=False, i=i: self.
                                         on_reset_button_clicked(checked, i))

        self.backend.streams_updated.connect(self.data_updated)

        self.show()

    def data_updated(self):
        img = self.backend.consume_stream(self.backend.streams,
                                          f'dm{self.dm_number:02d}disp')

        if img is not None:
            img_min, img_max = self.compute_min_max(img, symetric=True)

            self.dm_view.setImage(img, img_min, img_max)

        for i in range(0, 12):
            img = self.backend.consume_stream(
                self.backend.streams, f'dm{self.dm_number:02d}disp{i:02d}')

            if img is not None:
                view = getattr(self, f'view_{i:02d}')
                view.setImage(img, img_min, img_max)

    def on_reset_button_clicked(self, checked, i):
        self.backend.reset_channel(self.dm_number, i)

    @Slot(bool)
    def on_reset_all_button_clicked(self, checked):
        self.backend.reset_dm(self.dm_number)

    def closeEvent(self, event):
        self.timer.stop()
        event.accept()
