import numpy as np

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import QLabel, QLineEdit, QPushButton

from guis.kalao.mixins import BackendActionMixin
from guis.kalao.ui_loader import loadUi
from guis.kalao.widgets import KalAOStatusIndicator, KalAOWidget
from guis.windows.dm_channels import DMChannelsWindow
from guis.windows.dm_direct_control import DMDirectControl
from guis.windows.ttm_direct_control import TTMDirectControl

from kalao.definitions.enums import (FlipMirrorPosition, ServiceAction,
                                     ShutterState)

import config


class EngineeringWidget(KalAOWidget, BackendActionMixin):
    dm_channels = None
    ttm_channels = None
    dm_calibration = None
    ttm_calibration = None
    dm_direct_control = None
    ttm_direct_control = None

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

        self.services_widgets = {}
        for i, service in enumerate(config.Systemd.services.values()):
            label = QLabel(service['unit'].removeprefix('kalao_').removesuffix(
                '.service').replace('-', ' ').title())
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

            lineedit = QLineEdit()
            lineedit.setReadOnly(True)

            indicator = KalAOStatusIndicator()

            self.services_widgets[service['unit']] = {
                'lineedit': lineedit,
                'indicator': indicator
            }

            self.services_groupbox.layout().addWidget(label, i, 0)
            self.services_groupbox.layout().addWidget(lineedit, i, 2)

            indicator.setFixedSize(25, 25)
            self.services_groupbox.layout().addWidget(indicator, i, 1)

            for j, action in enumerate([
                    ServiceAction.START, ServiceAction.STOP,
                    ServiceAction.RESTART, ServiceAction.KILL,
                    ServiceAction.RELOAD
            ]):
                button = QPushButton(action.value.title())
                button.clicked.connect(lambda checked=False, unit=service[
                    'unit'], action=action: self.on_service_action_clicked(
                        checked, unit, action))
                self.services_groupbox.layout().addWidget(button, i, 3 + j)

                if action == ServiceAction.RELOAD and service[
                        'unit'] != "kalao_cacao.service":
                    button.setEnabled(False)

        self.services_groupbox.layout().setColumnStretch(0, 0)
        self.services_groupbox.layout().setColumnStretch(1, 0)
        self.services_groupbox.layout().setColumnStretch(2, 1)
        self.services_groupbox.layout().setColumnStretch(3, 1)
        self.services_groupbox.layout().setColumnStretch(4, 1)
        self.services_groupbox.layout().setColumnStretch(5, 1)
        self.services_groupbox.layout().setColumnStretch(6, 1)
        self.services_groupbox.layout().setColumnStretch(7, 1)

        backend.data_updated.connect(self.data_updated)

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

        adc1_angle = self.backend.consume_plc(data, 'adc1_angle')
        if adc1_angle is not None:
            self.adc1_spinbox.setValue(adc1_angle)

        adc2_angle = self.backend.consume_plc(data, 'adc2_angle')
        if adc2_angle is not None:
            self.adc2_spinbox.setValue(adc2_angle)

        for i, service in enumerate(config.Systemd.services.values()):
            status = self.backend.consume_service(data, service['unit'])
            if status is not None:
                widgets = self.services_widgets[service['unit']]
                widgets['lineedit'].setText(f'{status[0]} | {status[1]}')
                widgets['indicator'].setStatus(status[0] == 'active')

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

    @Slot(float)
    def on_adc1_spinbox_valueChanged(self, d):
        self.action_send(self.adc1_spinbox, self.backend.set_adc1_position, d)

    @Slot(float)
    def on_adc2_spinbox_valueChanged(self, d):
        self.action_send(self.adc2_spinbox, self.backend.set_adc2_position, d)

    @Slot(bool)
    def on_dm_channels_button_clicked(self, checked):
        if self.dm_channels is not None:
            self.dm_channels.show()
            self.dm_channels.activateWindow()
        else:
            self.dm_channels = DMChannelsWindow(self.backend, 1)

    @Slot(bool)
    def on_ttm_channels_button_clicked(self, checked):
        if self.ttm_channels is not None:
            self.ttm_channels.show()
            self.ttm_channels.activateWindow()
        else:
            self.ttm_channels = DMChannelsWindow(self.backend, 2)

    @Slot(bool)
    def on_dm_calibration_button_clicked(self, checked):
        if self.dm_calibration is not None:
            self.dm_calibration.show()
            self.dm_calibration.activateWindow()
        else:
            from guis.windows.calibration import CalibrationWindow
            self.dm_calibration = CalibrationWindow('dm', 1, (11, 22),
                                                    (12, 12))

    @Slot(bool)
    def on_ttm_calibration_button_clicked(self, checked):
        if self.ttm_calibration is not None:
            self.ttm_calibration.show()
            self.ttm_calibration.activateWindow()
        else:
            from guis.windows.calibration import CalibrationWindow
            self.ttm_calibration = CalibrationWindow('ttm', 2, (12, 12),
                                                     (1, 2))

    @Slot(bool)
    def on_dm_direct_control_button_clicked(self, checked):
        if self.dm_direct_control is not None:
            self.dm_direct_control.show()
            self.dm_direct_control.activateWindow()
        else:
            self.dm_direct_control = DMDirectControl(self.backend)

    @Slot(bool)
    def on_ttm_direct_control_button_clicked(self, checked):
        if self.ttm_direct_control is not None:
            self.ttm_direct_control.show()
            self.ttm_direct_control.activateWindow()
        else:
            self.ttm_direct_control = TTMDirectControl(self.backend)

    def on_service_action_clicked(self, checked, unit, action):
        self.backend.service_action(unit, action)
