import numpy as np

from PySide6.QtCore import QTimer, Slot

from guis.utils import colormaps
from guis.utils.mixins import (BackendActionMixin, BackendDataMixin,
                               MinMaxMixin, SceneHoverMixin)
from guis.utils.ui_loader import loadUi
from guis.utils.widgets import KMainWindow

import config


class DMChannelsWindow(KMainWindow, BackendActionMixin, MinMaxMixin,
                       SceneHoverMixin, BackendDataMixin):
    associated_stream = config.Streams.DM
    image_info = config.Images.dm01disp

    data_unit = ' µm'
    data_precision = 3

    axis_unit = ' px'
    axis_precision = 0

    def __init__(self, backend, dm_number, parent=None):
        super().__init__(parent)

        self.dm_number = dm_number
        self.backend = backend

        loadUi('dm_channels.ui', self)
        self.resize(950, 850)

        self.channels_timer = QTimer(parent=self)
        self.channels_timer.setInterval(
            int(1000 / config.GUI.refreshrate_streams))

        if dm_number == config.AO.DM_loop_number:
            prefix = 'DM_'
            self.disp_name = config.Streams.DM

            self.backend.streams_channels_dm_updated.connect(
                self.streams_channels_updated)
            self.channels_timer.timeout.connect(
                self.backend.streams_channels_dm)
        elif dm_number == config.AO.TTM_loop_number:
            self.associated_stream = config.Streams.TTM
            self.image_info = config.Images.dm02disp
            self.data_unit = ' mrad'
            self.data_precision = 2
            self.title_label.setText(self.title_label.text().replace(
                "Deformable Mirror", "Tip-Tilt Mirror"))
            self.setWindowTitle(self.windowTitle().replace(
                "Deformable Mirror", "Tip-Tilt Mirror"))

            prefix = 'TTM_'
            self.disp_name = config.Streams.TTM

            self.backend.streams_channels_ttm_updated.connect(
                self.streams_channels_updated)
            self.channels_timer.timeout.connect(
                self.backend.streams_channels_ttm)
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

            stroke_label = getattr(self, f'stroke_label_{i:02d}')
            stroke_label.updateText(min=np.nan, max=np.nan,
                                    unit=self.data_unit)

            self.reset_buttons[i] = reset_button
            view_list.append(view)

        self.init_minmax(view_list, symetric=True)

        for key, value in config.Streams.__dict__.items():
            if key.startswith(prefix):
                name = key.removeprefix(prefix).replace('_', ' ').title()
                value = value.removeprefix(self.disp_name)

                if name == 'Ncpa':
                    name = 'NCPA'

                label = getattr(self, f'info_label_{value}')
                label.setText(name)

        self.hovered.connect(self.info_to_statusbar)

        self.channels_timer.start()

        self.show()
        self.center()
        self.setFixedSize(self.size())

    def streams_channels_updated(self, data):
        img = self.consume_stream(data, f'{self.disp_name}')

        if img is not None:
            img_min, img_max = self.compute_min_max(img)

            self.dm_view.setImage(img, img_min, img_max)

        for i in range(0, 12):
            img = self.consume_stream(data, f'{self.disp_name}{i:02d}')

            if img is not None:
                view = getattr(self, f'view_{i:02d}')
                view.setImage(img, img_min, img_max)

                stroke_label = getattr(self, f'stroke_label_{i:02d}')
                stroke_label.updateText(min=img.min(), max=img.max(),
                                        unit=self.data_unit)

    def on_reset_button_clicked(self, checked, i):
        self.action_send(self.reset_buttons[i], self.backend.channels_reset,
                         dm_number=self.dm_number, channel=i)

    @Slot(bool)
    def on_reset_all_button_clicked(self, checked):
        self.action_send(self.reset_all_button, self.backend.channels_resetall,
                         dm_number=self.dm_number)

    def closeEvent(self, event):
        self.channels_timer.stop()
        event.accept()

    def showEvent(self, event):
        self.channels_timer.start()
        event.accept()
