import numpy as np

from PySide6.QtCore import Qt, Slot

from guis.kalao.mixins import BackendActionMixin
from guis.kalao.ui_loader import loadUi
from guis.kalao.widgets import KalAOWidget
from guis.windows.dm_channels import DMChannelsWindow

from kalao.definitions.enums import FlipMirrorPosition, ShutterState

import config


class EngineeringWidget(KalAOWidget, BackendActionMixin):
    def __init__(self, backend, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.backend = backend

        loadUi('engineering.ui', self)
        self.resize(600, 400)

        for state in ShutterState:
            if state != ShutterState.ERROR:
                self.shutter_combobox.addItem(state, state)

        for position in FlipMirrorPosition:
            if position != FlipMirrorPosition.ERROR:
                self.flipmirror_combobox.addItem(position, position)

        for filter in config.FilterWheel.position_list:
            self.filterwheel_combobox.addItem(self.filter_display_name(filter),
                                              filter)

        backend.streams_updated.connect(self.data_updated)

    def filter_display_name(self, filter):
        name = config.FilterWheel.filter_infos[filter]['name']
        start = config.FilterWheel.filter_infos[filter]['start']
        end = config.FilterWheel.filter_infos[filter]['end']

        if np.isinf(start):
            start_str = '-∞'
        else:
            start_str = f'{start*1e9:.0f} nm'

        if np.isinf(end):
            end_str = '∞'
        else:
            end_str = f'{end*1e9:.0f} nm'

        if np.isnan(start) and np.isnan(end):
            return name
        else:
            return f'{name} ({start_str} – {end_str})'

    def data_updated(self, data):
        print(data['plc'])

        shutter_state = self.backend.consume_plc(data, 'shutter_state')
        if shutter_state is not None:
            self.shutter_combobox.setCurrentIndex(
                self.shutter_combobox.findData(shutter_state))

        flip_mirror_position = self.backend.consume_plc(
            data, 'flip_mirror_position')
        if shutter_state is not None:
            self.flipmirror_combobox.setCurrentIndex(
                self.flipmirror_combobox.findData(flip_mirror_position))

        calib_unit_position = self.backend.consume_plc(data,
                                                       'calib_unit_position')
        if calib_unit_position is not None:
            self.calibunit_spinbox.setValue(calib_unit_position)

        tungsten_state = self.backend.consume_plc(data, 'tungsten_state')
        if tungsten_state is not None:
            if tungsten_state == 'ON':
                self.tungsten_enabled_checkbox.setCheckState(Qt.Checked)
            else:
                self.tungsten_enabled_checkbox.setCheckState(Qt.Unchecked)

        laser_state = self.backend.consume_plc(data, 'laser_state')
        if laser_state is not None:
            if laser_state == 'ON':
                self.laser_enabled_checkbox.setCheckState(Qt.Checked)
            else:
                self.laser_enabled_checkbox.setCheckState(Qt.Unchecked)

        laser_power = self.backend.consume_plc(data, 'laser_power')
        if laser_power is not None:
            self.laser_intensity_spinbox.setValue(laser_power)

        filterwheel_filter_name = self.backend.consume_plc(
            data, 'filterwheel_filter_name')
        if filterwheel_filter_name is not None:
            self.filterwheel_combobox.setCurrentIndex(
                self.filterwheel_combobox.findData(filterwheel_filter_name))

    @Slot(int)
    def on_shutter_combobox_currentIndexChanged(self, index):
        self.action_send(self.shutter_combobox, self.backend.set_shutter_state,
                         self.shutter_combobox.currentData())

    @Slot(int)
    def on_flipmirror_combobox_currentIndexChanged(self, index):
        self.action_send(self.flipmirror_combobox,
                         self.backend.set_flipmirror_position,
                         self.flipmirror_combobox.currentData())

    @Slot(float)
    def on_calibunit_spinbox_valueChanged(self, d):
        self.action_send(self.calibunit_spinbox,
                         self.backend.set_calibunit_position, d)

    @Slot(int)
    def on_tungsten_enabled_checkbox_stateChanged(self, state):
        self.action_send(self.tungsten_enabled_checkbox,
                         self.backend.set_tungsten_state,
                         Qt.CheckState(state) == Qt.Checked)

    @Slot(int)
    def on_laser_enabled_checkbox_stateChanged(self, state):
        self.action_send(self.laser_enabled_checkbox,
                         self.backend.set_laser_state,
                         Qt.CheckState(state) == Qt.Checked)

    @Slot(float)
    def on_laser_intensity_spinbox_valueChanged(self, d):
        self.action_send(self.laser_intensity_spinbox,
                         self.backend.set_laser_intensity, d)

    @Slot(int)
    def on_filterwheel_combobox_currentIndexChanged(self, index):
        self.action_send(self.filterwheel_combobox,
                         self.backend.set_filterwheel_filter,
                         self.filterwheel_combobox.currentData())

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
