from PySide6.QtCore import QTimer, Slot

from guis.kalao import colormaps
from guis.kalao.mixins import (BackendActionMixin, BackendDataMixin,
                               MinMaxMixin, SceneHoverMixin)
from guis.kalao.ui_loader import loadUi
from guis.kalao.widgets import KMainWindow

import config


class DMChannelsWindow(KMainWindow, BackendActionMixin, MinMaxMixin,
                       SceneHoverMixin, BackendDataMixin):
    associated_stream = config.Streams.DM
    stream_info = config.StreamInfo.dm01disp

    data_unit = ' µm'
    data_precision = 3

    axis_unit = ' px'
    axis_precision = 0

    def __init__(self, backend, dm_number, parent=None):
        super().__init__(parent)

        self.dm_number = dm_number
        self.backend = backend

        loadUi('dm_channels.ui', self)
        self.resize(400, 800)

        if dm_number == config.AO.DM_loop_number:
            prefix = 'DM_'
            disp_name = config.Streams.DM
        elif dm_number == config.AO.TTM_loop_number:
            self.associated_stream = config.Streams.TTM
            self.stream_info = config.StreamInfo.dm02disp
            self.data_unit = ' mrad'
            self.data_precision = 2
            self.title_label.setText(self.title_label.text().replace(
                "Deformable Mirror", "Tip-Tilt Mirror"))
            self.setWindowTitle(self.windowTitle().replace(
                "Deformable Mirror", "Tip-Tilt Mirror"))

            prefix = 'TTM_'
            disp_name = config.Streams.TTM
        else:
            raise Exception(f'Unknown DM number {dm_number}')

        self.dm_view.updateColormap(colormaps.CoolWarm())
        self.dm_view.hovered.connect(self.hover_xyv_to_str)

        view_list = [self.dm_view]
        self.reset_buttons = {}
        for i in range(0, 12):
            view = getattr(self, f'view_{i:02d}')
            view.hovered.connect(self.hover_xyv_to_str)
            view.updateColormap(colormaps.CoolWarm())

            reset_button = getattr(self, f'reset_button_{i:02d}')
            reset_button.clicked.connect(lambda checked=False, i=i: self.
                                         on_reset_button_clicked(checked, i))

            self.reset_buttons[i] = reset_button
            view_list.append(view)

        self.init_minmax(view_list, symetric=True)

        for key, value in config.Streams.__dict__.items():
            if key.startswith(prefix):
                name = key.removeprefix(prefix).replace('_', ' ').title()
                value = value.removeprefix(disp_name)

                if name == 'Ncpa':
                    name = 'NCPA'

                label = getattr(self, f'label_{value}_info')
                label.setText(name)

        self.hovered.connect(self.info_to_statusbar)

        self.backend.streams_dmdisp_updated.connect(
            self.streams_dmdisp_updated)

        self.channels_timer = QTimer(parent=self)
        self.channels_timer.setInterval(
            int(1000 / config.GUI.refreshrate_streams))
        self.channels_timer.timeout.connect(lambda: self.backend.
                                            get_streams_dmdisp(self.dm_number))
        self.channels_timer.start()

        self.show()
        self.center()
        self.setFixedSize(self.size())

    def streams_dmdisp_updated(self, data):
        img = self.consume_stream(data, f'dm{self.dm_number:02d}disp')

        if img is not None:
            img_min, img_max = self.compute_min_max(img)

            self.dm_view.setImage(img, img_min, img_max)

        for i in range(0, 12):
            img = self.consume_stream(data,
                                      f'dm{self.dm_number:02d}disp{i:02d}')

            if img is not None:
                view = getattr(self, f'view_{i:02d}')
                view.setImage(img, img_min, img_max)

    def on_reset_button_clicked(self, checked, i):
        self.action_send(self.reset_buttons[i],
                         self.backend.set_channels_reset, self.dm_number, i)

    @Slot(bool)
    def on_reset_all_button_clicked(self, checked):
        self.action_send(self.reset_all_button,
                         self.backend.set_channels_resetall, self.dm_number)

    def closeEvent(self, event):
        self.channels_timer.stop()
        event.accept()

    def showEvent(self, event):
        self.channels_timer.start()
        event.accept()
