from typing import Any

import numpy as np

from PySide6.QtCore import QTimer, Signal, Slot
from PySide6.QtGui import QCloseEvent, QShowEvent
from PySide6.QtWidgets import QWidget

from compiled.ui_dm_channels import Ui_DMChannelsWindow

from kalao.guis.backends.abstract import AbstractBackend
from kalao.guis.utils import colormaps
from kalao.guis.utils.mixins import (BackendActionMixin, BackendDataMixin,
                                     MinMaxMixin)
from kalao.guis.utils.widgets import KMainWindow

import config


class DMChannelsWindow(KMainWindow, BackendActionMixin, MinMaxMixin,
                       BackendDataMixin):
    image_info = config.Images.dm01disp

    data_unit = ' µm'
    data_precision = 3

    axis_unit = ' px'
    axis_precision = 0

    img_min = np.nan
    img_max = np.nan

    hovered = Signal(str)

    def __init__(self, backend: AbstractBackend, dm_number: int,
                 parent: QWidget = None) -> None:
        super().__init__(parent)

        self.dm_number = dm_number
        self.backend = backend

        self.ui = Ui_DMChannelsWindow()
        self.ui.setupUi(self)

        self.resize(950, 850)

        self.channels_timer = QTimer(parent=self)
        self.channels_timer.setInterval(
            int(1000 / config.GUI.refreshrate_streams))

        if dm_number == config.AO.DM_loop_number:
            prefix = 'DM_'
            self.disp_stream = config.SHM.DM
            self.commands_stream = config.SHM.COMMANDS_DM
            self.data_unit = ' µm'
            self.mask = np.full(config.DM.shape, False)
            self.mask[0, 0] = True
            self.mask[0, -1] = True
            self.mask[-1, 0] = True
            self.mask[-1, -1] = True

            self.backend.streams_channels_dm_updated.connect(
                self.streams_channels_updated)
            self.channels_timer.timeout.connect(
                self.backend.streams_channels_dm)
        elif dm_number == config.AO.TTM_loop_number:
            self.image_info = config.Images.dm02disp
            self.data_unit = ' mrad'
            self.data_precision = 2
            self.ui.title_label.setText(self.ui.title_label.text().replace(
                'Deformable Mirror', 'Tip-Tilt Mirror'))
            self.setWindowTitle(self.windowTitle().replace(
                'Deformable Mirror', 'Tip-Tilt Mirror'))

            prefix = 'TTM_'
            self.disp_stream = config.SHM.TTM
            self.commands_stream = config.SHM.COMMANDS_TTM
            self.mask = np.full((2, ), False)

            self.backend.streams_channels_ttm_updated.connect(
                self.streams_channels_updated)
            self.channels_timer.timeout.connect(
                self.backend.streams_channels_ttm)
        else:
            raise IndexError(f'Unknown DM number {dm_number}')

        self.ui.dm_view.set_data_md(self.data_unit, 2)
        self.ui.dm_view.set_axis_md('', 0)
        self.ui.dm_view.updateColormap(colormaps.CoolWarm())
        self.ui.dm_view.hovered_str.connect(lambda string: self.hovered.emit(
            string))

        self.ui.stroke_label_dm.updateText(min=np.nan, max=np.nan,
                                           unit=self.data_unit)

        self.ui.commands_view.set_data_md('', 2)
        self.ui.commands_view.set_axis_md('', 0)
        self.ui.commands_view.updateColormap(colormaps.CoolWarmTransparent())
        self.ui.commands_view.hovered_str.connect(lambda string: self.hovered.
                                                  emit(string))

        self.ui.stroke_label_commands.updateText(min=np.nan, max=np.nan,
                                                 unit='')

        view_list = [self.ui.dm_view]
        self.reset_buttons = []
        for i in range(0, 12):
            view = getattr(self.ui, f'view_{i:02d}')
            view.set_data_md(self.data_unit, 2)
            view.set_axis_md('', 0)
            view.updateColormap(colormaps.CoolWarm())
            view.hovered_str.connect(lambda string: self.hovered.emit(string))

            reset_button = getattr(self.ui, f'reset_button_{i:02d}')
            reset_button.clicked.connect(lambda checked=False, _i=i: self.
                                         on_reset_button_clicked(checked, _i))

            stroke_label = getattr(self.ui, f'stroke_label_{i:02d}')
            stroke_label.updateText(min=np.nan, max=np.nan,
                                    unit=self.data_unit)

            self.reset_buttons.append(reset_button)
            view_list.append(view)

        self.init_minmax(view_list, symetric=True)

        for key, value in vars(config.SHM).items():
            if key.startswith(prefix):
                name = key.removeprefix(prefix).replace('_', ' ').title()
                value = value.removeprefix(self.disp_stream)

                if name == 'Ncpa':
                    name = 'NCPA'

                label = getattr(self.ui, f'info_label_{value}')
                label.setText(name)

        self.hovered.connect(self.info_to_statusbar)

        self.channels_timer.start()

        self.show()
        self.center()
        self.setFixedSize(self.size())

    def streams_channels_updated(self, data: dict[str, Any]) -> None:
        img = self.consume_shm(data, self.disp_stream)
        if img is not None:
            self.img_min, self.img_max = self.compute_min_max(img)

            self.ui.dm_view.setImage(img, self.img_min, self.img_max)
            self.ui.stroke_label_dm.updateText(min=img.min(), max=img.max(),
                                               unit=self.data_unit)

        img = self.consume_shm(data, self.commands_stream)
        if img is not None:
            img = np.ma.masked_array(img, self.mask, fill_value=np.nan)
            self.ui.commands_view.setImage(img, -1, 1)
            self.ui.stroke_label_commands.updateText(min=img.min(),
                                                     max=img.max(), unit='')

        for i in range(0, 12):
            img = self.consume_shm(data, f'{self.disp_stream}{i:02d}')

            if img is not None:
                view = getattr(self.ui, f'view_{i:02d}')
                view.setImage(img, self.img_min, self.img_max)

                stroke_label = getattr(self.ui, f'stroke_label_{i:02d}')
                stroke_label.updateText(min=img.min(), max=img.max(),
                                        unit=self.data_unit)

    def on_reset_button_clicked(self, checked: bool, i: int) -> None:
        self.action_send(self.reset_buttons[i], self.backend.channels_reset,
                         dm_number=self.dm_number, channel=i)

    @Slot(bool)
    def on_reset_all_button_clicked(self, checked: bool) -> None:
        self.action_send(self.reset_buttons + [self.ui.reset_all_button],
                         self.backend.channels_resetall,
                         dm_number=self.dm_number)

    def closeEvent(self, event: QCloseEvent) -> None:
        self.channels_timer.stop()

        return super().closeEvent(event)

    def showEvent(self, event: QShowEvent) -> None:
        self.channels_timer.start()

        return super().showEvent(event)
