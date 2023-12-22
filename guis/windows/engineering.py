import numpy as np

from PySide6.QtCore import QSignalBlocker, Qt, Slot
from PySide6.QtWidgets import QLabel, QLineEdit, QPushButton

from guis.kalao.definitions import Color
from guis.kalao.mixins import BackendActionMixin, BackendDataMixin
from guis.kalao.ui_loader import loadUi
from guis.kalao.widgets import KalAOStatusIndicator, KalAOWidget
from guis.windows.dm_channels import DMChannelsWindow
from guis.windows.dm_direct_control import DMDirectControl
from guis.windows.ttm_direct_control import TTMDirectControl

from kalao.definitions.enums import (FilterwheelStatus, FlipMirrorPosition,
                                     IPPowerStatus, LaserState, PLCStatus,
                                     ServiceAction, ShutterState,
                                     TungstenState)

import config


class EngineeringWidget(KalAOWidget, BackendActionMixin, BackendDataMixin):
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

        with QSignalBlocker(self.shutter_combobox):
            for state in [ShutterState.CLOSED, ShutterState.OPEN]:
                self.shutter_combobox.addItem(state, state)

        with QSignalBlocker(self.flipmirror_combobox):
            for position in [FlipMirrorPosition.DOWN, FlipMirrorPosition.UP]:
                self.flipmirror_combobox.addItem(position, position)

        with QSignalBlocker(self.filterwheel_combobox):
            for filter in config.FilterWheel.position_list:
                self.filterwheel_combobox.addItem(
                    self.filter_display_name(filter), filter)

        s = 5
        self.services_widgets = {}
        for i, service in enumerate(config.Systemd.services.values()):
            label = QLabel(service['unit'].removeprefix('kalao_').removesuffix(
                '.service').replace('-', ' ').title())
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

            lineedit = QLineEdit()
            lineedit.setReadOnly(True)
            lineedit.setToolTipDuration(2147483647)

            indicator = KalAOStatusIndicator()

            self.services_widgets[service['unit']] = {
                'lineedit': lineedit,
                'indicator': indicator
            }

            self.services_groupbox.layout().addWidget(label, i, 0,
                                                      Qt.AlignVCenter)
            self.services_groupbox.layout().addWidget(lineedit, i, 2,
                                                      Qt.AlignVCenter)

            indicator.setFixedSize(20, 20)
            self.services_groupbox.layout().addWidget(indicator, i, 1,
                                                      Qt.AlignVCenter)

            for j, action in enumerate([
                    ServiceAction.START, ServiceAction.STOP,
                    ServiceAction.RESTART, ServiceAction.KILL,
                    ServiceAction.RELOAD
            ]):
                button = QPushButton(action.value.title())
                button.clicked.connect(
                    lambda checked=False, unit=service['unit'], action=action:
                    self.on_set_services_action_clicked(checked, unit, action))
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
        shutter_state = self.consume_dict(data, 'plc', 'shutter_state')
        if shutter_state is not None:
            with QSignalBlocker(self.shutter_combobox):
                self.shutter_combobox.setCurrentIndex(
                    self.shutter_combobox.findData(shutter_state))

            if shutter_state == ShutterState.OPEN:
                self.shutter_indicator.setStatus(Color.GREEN,
                                                 shutter_state.name)
            elif shutter_state == ShutterState.CLOSED:
                self.shutter_indicator.setStatus(Color.BLACK,
                                                 shutter_state.name)
            else:  # ERROR
                self.shutter_indicator.setStatus(Color.RED, shutter_state.name)

        flip_mirror_position = self.consume_dict(data, 'plc',
                                                 'flip_mirror_position')
        if flip_mirror_position is not None:
            with QSignalBlocker(self.flipmirror_combobox):
                self.flipmirror_combobox.setCurrentIndex(
                    self.flipmirror_combobox.findData(flip_mirror_position))

            if flip_mirror_position == FlipMirrorPosition.DOWN:
                self.flipmirror_indicator.setStatus(Color.BLACK,
                                                    flip_mirror_position.name)
            elif flip_mirror_position == FlipMirrorPosition.UP:
                self.flipmirror_indicator.setStatus(Color.YELLOW,
                                                    flip_mirror_position.name)
            elif flip_mirror_position == FlipMirrorPosition.UNKNOWN:
                self.flipmirror_indicator.setStatus(Color.BLUE,
                                                    flip_mirror_position.name)
            else:  # ERROR
                self.flipmirror_indicator.setStatus(Color.RED,
                                                    flip_mirror_position.name)

        calib_unit_position = self.consume_dict(data, 'plc',
                                                'calib_unit_position')
        if calib_unit_position is not None:
            with QSignalBlocker(self.calibunit_spinbox):
                self.calibunit_spinbox.setValue(calib_unit_position)

        calib_unit_state = self.consume_dict(data, 'plc', 'calib_unit_state')
        if calib_unit_state is not None:
            if calib_unit_state == PLCStatus.STANDING:
                self.calibunit_indicator.setStatus(Color.GREEN,
                                                   calib_unit_state.name)
            elif calib_unit_state == PLCStatus.MOVING:
                self.calibunit_indicator.setStatus(Color.BLUE,
                                                   calib_unit_state.name)
            elif calib_unit_state == PLCStatus.INITIALISING:
                self.calibunit_indicator.setStatus(Color.ORANGE,
                                                   calib_unit_state.name)
            else:  # DISABLED, UNINITIALISED, ERROR, UNKNOWN
                self.calibunit_indicator.setStatus(Color.RED,
                                                   calib_unit_state.name)

            if calib_unit_state in [PLCStatus.MOVING, PLCStatus.INITIALISING]:
                self.calibunit_spinbox.setEnabled(False)
            else:
                self.calibunit_spinbox.setEnabled(True)

        tungsten_state = self.consume_dict(data, 'plc', 'tungsten_state')
        if tungsten_state is not None:
            with QSignalBlocker(self.tungsten_state_checkbox):
                self.tungsten_state_checkbox.setChecked(
                    tungsten_state == TungstenState.ON)

            if tungsten_state == TungstenState.ON:
                self.tungsten_state_indicator.setStatus(
                    Color.YELLOW, tungsten_state.name)
            elif tungsten_state == TungstenState.OFF:
                self.tungsten_state_indicator.setStatus(
                    Color.BLACK, tungsten_state.name)
            else:  # ERROR
                self.tungsten_state_indicator.setStatus(
                    Color.RED, tungsten_state.name)

        laser_state = self.consume_dict(data, 'plc', 'laser_state')
        if laser_state is not None:
            with QSignalBlocker(self.laser_state_checkbox):
                self.laser_state_checkbox.setChecked(
                    laser_state == LaserState.ON)

        laser_power = self.consume_dict(data, 'plc', 'laser_power')
        if laser_power is not None:
            with QSignalBlocker(self.laser_power_spinbox):
                self.laser_power_spinbox.setValue(laser_power)

        if laser_power is not None or laser_state is not None:
            laser_state = self.consume_dict(data, 'plc', 'laser_state',
                                            force=True)
            laser_power = self.consume_dict(data, 'plc', 'laser_power',
                                            force=True)

            if laser_state == LaserState.ON and laser_power > 0:
                self.laser_state_indicator.setStatus(Color.YELLOW,
                                                     laser_state.name)
                self.laser_power_indicator.setStatus(Color.YELLOW, laser_power)
            elif laser_state == LaserState.OFF or laser_power == 0:
                self.laser_state_indicator.setStatus(Color.BLACK,
                                                     laser_state.name)
                self.laser_power_indicator.setStatus(Color.BLACK, laser_power)
            else:  # ERROR or < 0
                self.laser_state_indicator.setStatus(Color.RED,
                                                     laser_state.name)
                self.laser_power_indicator.setStatus(Color.RED, laser_power)

        filterwheel_filter_name = self.consume_dict(data, 'plc',
                                                    'filterwheel_filter_name')
        if filterwheel_filter_name is not None:
            with QSignalBlocker(self.filterwheel_combobox):
                self.filterwheel_combobox.setCurrentIndex(
                    self.filterwheel_combobox.findData(
                        filterwheel_filter_name))

            if filterwheel_filter_name != FilterwheelStatus.ERROR_NAME:
                self.filterwheel_indicator.setStatus(Color.GREEN,
                                                     filterwheel_filter_name)
            else:  # ERROR
                self.filterwheel_indicator.setStatus(Color.RED,
                                                     filterwheel_filter_name)

        adc1_angle = self.consume_dict(data, 'plc', 'adc1_angle')
        if adc1_angle is not None:
            with QSignalBlocker(self.adc1_spinbox):
                self.adc1_spinbox.setValue(adc1_angle)

        adc1_state = self.consume_dict(data, 'plc', 'adc1_state')
        if adc1_state is not None:
            if adc1_state == PLCStatus.STANDING:
                self.adc1_indicator.setStatus(Color.GREEN, adc1_state.name)
            elif adc1_state == PLCStatus.MOVING:
                self.adc1_indicator.setStatus(Color.BLUE, adc1_state.name)
            elif adc1_state == PLCStatus.INITIALISING:
                self.adc1_indicator.setStatus(Color.ORANGE, adc1_state.name)
            else:  # DISABLED, UNINITIALISED, ERROR, UNKNOWN
                self.adc1_indicator.setStatus(Color.RED, adc1_state.name)

            if adc1_state in [PLCStatus.MOVING, PLCStatus.INITIALISING]:
                self.adc1_spinbox.setEnabled(False)
            else:
                self.adc1_spinbox.setEnabled(True)

        adc2_angle = self.consume_dict(data, 'plc', 'adc2_angle')
        if adc2_angle is not None:
            with QSignalBlocker(self.adc2_spinbox):
                self.adc2_spinbox.setValue(adc2_angle)

        adc2_state = self.consume_dict(data, 'plc', 'adc2_state')
        if adc2_state is not None:
            if adc2_state == PLCStatus.STANDING:
                self.adc2_indicator.setStatus(Color.GREEN, adc2_state.name)
            elif adc2_state == PLCStatus.MOVING:
                self.adc2_indicator.setStatus(Color.BLUE, adc2_state.name)
            elif adc2_state == PLCStatus.INITIALISING:
                self.adc2_indicator.setStatus(Color.ORANGE, adc2_state.name)
            else:  # DISABLED, UNINITIALISED, ERROR, UNKNOWN
                self.adc2_indicator.setStatus(Color.RED, adc2_state.name)

            if adc2_state in [PLCStatus.MOVING, PLCStatus.INITIALISING]:
                self.adc2_spinbox.setEnabled(False)
            else:
                self.adc2_spinbox.setEnabled(True)

        ippower_rtc_status = self.consume_dict(data, 'ippower',
                                               'ippower_rtc_status')
        if ippower_rtc_status is not None:
            if ippower_rtc_status == IPPowerStatus.ON:
                self.ippower_rtc_indicator.setStatus(Color.GREEN,
                                                     ippower_rtc_status.name)
            elif ippower_rtc_status == IPPowerStatus.OFF:
                self.ippower_rtc_indicator.setStatus(Color.BLACK,
                                                     ippower_rtc_status.name)
            else:
                self.ippower_rtc_indicator.setStatus(Color.RED,
                                                     ippower_rtc_status.name)

        ippower_bench_status = self.consume_dict(data, 'ippower',
                                                 'ippower_bench_status')
        if ippower_bench_status is not None:
            if ippower_bench_status == IPPowerStatus.ON:
                self.ippower_bench_indicator.setStatus(
                    Color.GREEN, ippower_bench_status.name)
            elif ippower_bench_status == IPPowerStatus.OFF:
                self.ippower_bench_indicator.setStatus(
                    Color.BLACK, ippower_bench_status.name)
            else:
                self.ippower_bench_indicator.setStatus(
                    Color.RED, ippower_bench_status.name)

        ippower_dm_status = self.consume_dict(data, 'ippower',
                                              'ippower_dm_status')
        if ippower_dm_status is not None:
            if ippower_dm_status == IPPowerStatus.ON:
                self.ippower_dm_indicator.setStatus(Color.GREEN,
                                                    ippower_dm_status.name)
            elif ippower_dm_status == IPPowerStatus.OFF:
                self.ippower_dm_indicator.setStatus(Color.BLACK,
                                                    ippower_dm_status.name)
            else:
                self.ippower_dm_indicator.setStatus(Color.RED,
                                                    ippower_dm_status.name)

        exposure_time = self.consume_dict(data, 'fli', 'exposure_time')
        if exposure_time is not None:
            with QSignalBlocker(self.fli_exposure_time_spinbox):
                self.fli_exposure_time_spinbox.setValue(exposure_time)

        remaining_time = self.consume_dict(data, 'fli', 'remaining_time')
        if remaining_time is not None:
            with QSignalBlocker(self.fli_remaining_time_spinbox):
                self.fli_remaining_time_spinbox.setValue(remaining_time)

            if remaining_time < 0.001:
                self.fli_new_image_button.setEnabled(True)
                self.fli_exposure_time_spinbox.setEnabled(True)
            else:
                self.fli_new_image_button.setEnabled(False)
                self.fli_exposure_time_spinbox.setEnabled(False)

        for i, service in enumerate(config.Systemd.services.values()):
            status = self.consume_dict(data, 'services', service['unit'])
            if status is not None:
                widgets = self.services_widgets[service['unit']]
                widgets['lineedit'].setText(f'{status[0]} | {status[1]}')
                widgets['lineedit'].setToolTip(
                    status[2].astimezone().strftime('%H:%M:%S %d-%m-%Y'))

                if status[0] in ['active']:
                    widgets['indicator'].setStatus(Color.GREEN, status[0])
                elif status[0] in ['inactive']:
                    widgets['indicator'].setStatus(Color.BLACK, status[0])
                elif status[0] in ['activating', 'deactivating', 'reloading']:
                    widgets['indicator'].setStatus(Color.ORANGE, status[0])
                else:  # failed
                    widgets['indicator'].setStatus(Color.RED, status[0])

    @Slot(int)
    def on_shutter_combobox_currentIndexChanged(self, index):
        self.action_send(self.shutter_combobox,
                         self.backend.set_plc_shutter_state,
                         self.shutter_combobox.currentData())

    @Slot(int)
    def on_flipmirror_combobox_currentIndexChanged(self, index):
        self.action_send(self.flipmirror_combobox,
                         self.backend.set_plc_flipmirror_position,
                         self.flipmirror_combobox.currentData())

    @Slot(float)
    def on_calibunit_spinbox_valueChanged(self, d):
        self.action_send(self.calibunit_spinbox,
                         self.backend.set_plc_calibunit_position, d)

    @Slot(int)
    def on_tungsten_state_checkbox_stateChanged(self, state):
        self.action_send(self.tungsten_state_checkbox,
                         self.backend.set_plc_tungsten_state,
                         Qt.CheckState(state) == Qt.Checked)

    @Slot(int)
    def on_laser_state_checkbox_stateChanged(self, state):
        self.action_send(self.laser_state_checkbox,
                         self.backend.set_plc_laser_state,
                         Qt.CheckState(state) == Qt.Checked)

    @Slot(float)
    def on_laser_power_spinbox_valueChanged(self, d):
        self.action_send(self.laser_power_spinbox,
                         self.backend.set_plc_laser_power, d)

    @Slot(int)
    def on_filterwheel_combobox_currentIndexChanged(self, index):
        self.action_send(self.filterwheel_combobox,
                         self.backend.set_plc_filterwheel_filter,
                         self.filterwheel_combobox.currentData())

    @Slot(float)
    def on_adc1_spinbox_valueChanged(self, d):
        self.action_send(self.adc1_spinbox, self.backend.set_plc_adc_1_angle,
                         d)

    @Slot(float)
    def on_adc2_spinbox_valueChanged(self, d):
        self.action_send(self.adc2_spinbox, self.backend.set_plc_adc_2_angle,
                         d)

    @Slot(bool)
    def on_fli_new_image_button_clicked(self, checked):
        self.action_send(self.fli_new_image_button, self.backend.set_fli_image,
                         self.fli_exposure_time_spinbox.value())

    @Slot(bool)
    def on_fli_cancel_button_clicked(self, checked):
        self.action_send(self.fli_cancel_button, self.backend.get_fli_cancel)

    @Slot(bool)
    def on_ippower_rtc_on_button_clicked(self, checked):
        self.action_send(self.ippower_rtc_on_button,
                         self.backend.get_ippower_rtc_on)

    @Slot(bool)
    def on_ippower_rtc_off_button_clicked(self, checked):
        self.action_send(self.ippower_rtc_off_button,
                         self.backend.get_ippower_rtc_off)

    @Slot(bool)
    def on_ippower_bench_on_button_clicked(self, checked):
        self.action_send(self.ippower_bench_on_button,
                         self.backend.get_ippower_bench_on)

    @Slot(bool)
    def on_ippower_bench_off_button_clicked(self, checked):
        self.action_send(self.ippower_bench_off_button,
                         self.backend.get_ippower_bench_off)

    @Slot(bool)
    def on_ippower_dm_on_button_clicked(self, checked):
        self.action_send(self.ippower_dm_on_button,
                         self.backend.get_ippower_dm_on)

    @Slot(bool)
    def on_ippower_dm_off_button_clicked(self, checked):
        self.action_send(self.ippower_dm_off_button,
                         self.backend.get_ippower_dm_off)

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
            self.dm_calibration = CalibrationWindow(self.backend, 'dm', 1,
                                                    (11, 22), (12, 12))

    @Slot(bool)
    def on_ttm_calibration_button_clicked(self, checked):
        if self.ttm_calibration is not None:
            self.ttm_calibration.show()
            self.ttm_calibration.activateWindow()
        else:
            from guis.windows.calibration import CalibrationWindow
            self.ttm_calibration = CalibrationWindow(self.backend, 'ttm', 2,
                                                     (12, 12), (1, 2))

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

    @Slot(bool)
    def on_centering_star_button_clicked(self, checked):
        self.action_send(self.centering_star_button,
                         self.backend.get_centering_star)

    @Slot(bool)
    def on_centering_laser_button_clicked(self, checked):
        self.action_send(self.centering_laser_button,
                         self.backend.get_centering_laser)

    def on_set_services_action_clicked(self, checked, unit, action):
        self.action_send([], self.backend.set_services_action, unit, action)
