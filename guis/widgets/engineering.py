from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from PySide6.QtCore import QEvent, QObject, QSignalBlocker, Signal, Slot
from PySide6.QtGui import Qt
from PySide6.QtWidgets import (QFileDialog, QLabel, QLineEdit, QMessageBox,
                               QPushButton)

from guis.kalao.definitions import Color
from guis.kalao.mixins import BackendActionMixin, BackendDataMixin
from guis.kalao.ui_loader import loadUi
from guis.kalao.widgets import KMessageBox, KStatusIndicator, KWidget
from guis.windows.dm_channels import DMChannelsWindow
from guis.windows.dm_direct_control import DMDirectControlWindow
from guis.windows.focus import FocusWindow
from guis.windows.ttm_direct_control import TTMDirectControlWindow

from kalao.definitions.enums import (FilterwheelStatus, FlipMirrorPosition,
                                     IPPowerStatus, LaserState, PLCStatus,
                                     RelayState, SequencerStatus,
                                     ServiceAction, ShutterState,
                                     TungstenState)

import config


class EngineeringWidget(KWidget, BackendActionMixin, BackendDataMixin):
    hovered = Signal(str)

    dm_channels = None
    ttm_channels = None
    dm_calibration = None
    ttm_calibration = None
    dm_direct_control = None
    ttm_direct_control = None
    focus_window = None

    def __init__(self, backend, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.backend = backend

        loadUi('engineering.ui', self)
        self.resize(600, 400)

        for key in dir(self):
            attr = getattr(self, key)

            if isinstance(attr, KStatusIndicator):
                attr.installEventFilter(self)

        with QSignalBlocker(self.shutter_combobox):
            for state in [ShutterState.CLOSED, ShutterState.OPEN]:
                self.shutter_combobox.addItem(state, state)

            self.shutter_combobox.setCurrentIndex(-1)

        with QSignalBlocker(self.flipmirror_combobox):
            for position in [FlipMirrorPosition.DOWN, FlipMirrorPosition.UP]:
                self.flipmirror_combobox.addItem(position, position)

            self.flipmirror_combobox.setCurrentIndex(-1)

        with QSignalBlocker(self.filterwheel_combobox):
            for filter in config.FilterWheel.position_list:
                self.filterwheel_combobox.addItem(
                    self.filter_display_name(filter), filter)

            self.filterwheel_combobox.setCurrentIndex(-1)

        self.services_widgets = {}
        for i, (key, service) in enumerate(config.Systemd.services.items()):
            label = QLabel(key)
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

            lineedit = QLineEdit()
            lineedit.setReadOnly(True)
            lineedit.setCursor(Qt.WhatsThisCursor)
            lineedit.installEventFilter(self)

            indicator = KStatusIndicator()
            indicator.setCursor(Qt.WhatsThisCursor)
            indicator.installEventFilter(self)

            self.services_widgets[service['unit']] = {
                'lineedit': lineedit,
                'indicator': indicator
            }

            self.services_layout.addWidget(label, i, 0, Qt.AlignVCenter)
            self.services_layout.addWidget(lineedit, i, 2, Qt.AlignVCenter)

            indicator.setFixedSize(20, 20)
            self.services_layout.addWidget(indicator, i, 1, Qt.AlignVCenter)

            for j, action in enumerate([
                    ServiceAction.START, ServiceAction.STOP,
                    ServiceAction.RESTART, ServiceAction.KILL,
                    ServiceAction.RELOAD
            ]):
                button = QPushButton(action.value.title())
                button.clicked.connect(lambda checked=False, unit=service[
                    'unit'], action=action: self.
                                       on_service_action_button_clicked(
                                           checked, unit, action))
                self.services_layout.addWidget(button, i, 3 + j)

                if action == ServiceAction.RELOAD and not service.get(
                        'reload-allowed', False):
                    button.setEnabled(False)

        self.services_layout.setColumnStretch(0, 0)
        self.services_layout.setColumnStretch(1, 0)
        self.services_layout.setColumnStretch(2, 2)
        self.services_layout.setColumnStretch(3, 1)
        self.services_layout.setColumnStretch(4, 1)
        self.services_layout.setColumnStretch(5, 1)
        self.services_layout.setColumnStretch(6, 1)
        self.services_layout.setColumnStretch(7, 1)

        backend.all_updated.connect(self.all_updated)

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

    def all_updated(self, data):
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

        flipmirror_position = self.consume_dict(data, 'plc',
                                                'flipmirror_position')
        if flipmirror_position is not None:
            with QSignalBlocker(self.flipmirror_combobox):
                self.flipmirror_combobox.setCurrentIndex(
                    self.flipmirror_combobox.findData(flipmirror_position))

            if flipmirror_position == FlipMirrorPosition.DOWN:
                self.flipmirror_indicator.setStatus(Color.BLACK,
                                                    flipmirror_position.name)
            elif flipmirror_position == FlipMirrorPosition.UP:
                self.flipmirror_indicator.setStatus(Color.YELLOW,
                                                    flipmirror_position.name)
            elif flipmirror_position == FlipMirrorPosition.UNKNOWN:
                self.flipmirror_indicator.setStatus(Color.BLUE,
                                                    flipmirror_position.name)
            else:  # ERROR
                self.flipmirror_indicator.setStatus(Color.RED,
                                                    flipmirror_position.name)

        calibunit_position = self.consume_dict(data, 'plc',
                                               'calibunit_position')
        if calibunit_position is not None:
            with QSignalBlocker(self.calibunit_spinbox):
                self.calibunit_spinbox.setValue(calibunit_position)

        calibunit_state = self.consume_dict(data, 'plc', 'calibunit_state')
        if calibunit_state is not None:
            if calibunit_state == PLCStatus.STANDING:
                self.calibunit_indicator.setStatus(Color.GREEN,
                                                   calibunit_state.name)
            elif calibunit_state == PLCStatus.MOVING:
                self.calibunit_indicator.setStatus(Color.BLUE,
                                                   calibunit_state.name)
            elif calibunit_state == PLCStatus.INITIALISING:
                self.calibunit_indicator.setStatus(Color.ORANGE,
                                                   calibunit_state.name)
            else:  # NOT_ENABLED, NOT_INITIALISED, ERROR, UNKNOWN
                self.calibunit_indicator.setStatus(Color.RED,
                                                   calibunit_state.name)

            if calibunit_state in [PLCStatus.MOVING, PLCStatus.INITIALISING]:
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
                self.laser_indicator.setStatus(
                    Color.YELLOW, f'{laser_state.name} & {laser_power}')
            elif laser_state == LaserState.OFF or laser_power == 0:
                self.laser_indicator.setStatus(
                    Color.BLACK, f'{laser_state.name} & {laser_power}')
            else:  # ERROR or < 0
                self.laser_indicator.setStatus(
                    Color.RED, f'{laser_state.name} & {laser_power}')

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
            else:  # NOT_ENABLED, NOT_INITIALISED, ERROR, UNKNOWN
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
            else:  # NOT_ENABLED, NOT_INITIALISED, ERROR, UNKNOWN
                self.adc2_indicator.setStatus(Color.RED, adc2_state.name)

            if adc2_state in [PLCStatus.MOVING, PLCStatus.INITIALISING]:
                self.adc2_spinbox.setEnabled(False)
            else:
                self.adc2_spinbox.setEnabled(True)

        pump_status = self.consume_dict(data, 'plc', 'pump_status')
        if pump_status is not None:
            with QSignalBlocker(self.pump_checkbox):
                self.pump_checkbox.setChecked(pump_status == RelayState.ON)

            if pump_status == RelayState.ON:
                self.pump_indicator.setStatus(Color.GREEN, pump_status.name)
            elif pump_status == RelayState.OFF:
                self.pump_indicator.setStatus(Color.BLACK, pump_status.name)
            else:
                self.pump_indicator.setStatus(Color.RED, pump_status.name)

        fan_status = self.consume_dict(data, 'plc', 'fan_status')
        if fan_status is not None:
            with QSignalBlocker(self.fan_checkbox):
                self.fan_checkbox.setChecked(fan_status == RelayState.ON)

            if fan_status == RelayState.ON:
                self.fan_indicator.setStatus(Color.GREEN, fan_status.name)
            elif fan_status == RelayState.OFF:
                self.fan_indicator.setStatus(Color.BLACK, fan_status.name)
            else:
                self.fan_indicator.setStatus(Color.RED, fan_status.name)

        heater_status = self.consume_dict(data, 'plc', 'heater_status')
        if heater_status is not None:
            with QSignalBlocker(self.heater_checkbox):
                self.heater_checkbox.setChecked(heater_status == RelayState.ON)

            if heater_status == RelayState.ON:
                self.heater_indicator.setStatus(Color.GREEN,
                                                heater_status.name)
            elif heater_status == RelayState.OFF:
                self.heater_indicator.setStatus(Color.BLACK,
                                                heater_status.name)
            else:
                self.heater_indicator.setStatus(Color.RED, heater_status.name)

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

        frames = self.consume_dict(data, 'fli', 'frames')
        if frames is not None:
            with QSignalBlocker(self.fli_frames_spinbox):
                self.fli_frames_spinbox.setValue(frames)

        remaining_frames = self.consume_dict(data, 'fli', 'remaining_frames')
        if remaining_frames is not None:
            with QSignalBlocker(self.fli_remaining_frames_spinbox):
                self.fli_remaining_frames_spinbox.setValue(remaining_frames)

            if remaining_frames == 0:
                self.fli_new_image_button.setEnabled(True)
                self.fli_exposure_time_spinbox.setEnabled(True)
                self.fli_frames_spinbox.setEnabled(True)
            else:
                self.fli_new_image_button.setEnabled(False)
                self.fli_exposure_time_spinbox.setEnabled(False)
                self.fli_frames_spinbox.setEnabled(False)

        maqtime = self.consume_stream_keyword(data, config.Streams.NUVU_RAW,
                                              '_MAQTIME', force=True)
        timestamp = self.consume_metadata(data, 'timestamp')
        if maqtime is not None:
            maqtime = datetime.fromtimestamp(maqtime / 1e6, tz=timezone.utc)
            time_since_last_frame = (timestamp - maqtime).total_seconds()
            if time_since_last_frame < config.WFS.acquisition_time_timeout:
                self.wfs_acquisition_indicator.setStatus(
                    Color.GREEN, time_since_last_frame)
            else:
                self.wfs_acquisition_indicator.setStatus(
                    Color.BLACK, time_since_last_frame)

        for i, service in enumerate(config.Systemd.services.values()):
            status = self.consume_dict(data, 'services', service['unit'])
            if status is not None:
                widgets = self.services_widgets[service['unit']]
                if status[1] != '':
                    widgets['lineedit'].setText(f'{status[0]} | {status[1]}')
                else:
                    widgets['lineedit'].setText(f'{status[0]}')
                widgets[
                    'lineedit'].hover_text = f'Since: {status[2].astimezone().strftime("%H:%M:%S %d-%m-%Y")}'

                if status[0] in ['active']:
                    widgets['indicator'].setStatus(Color.GREEN, status[0])
                elif status[0] in ['inactive']:
                    widgets['indicator'].setStatus(Color.BLACK, status[0])
                elif status[0] in ['activating', 'deactivating', 'reloading']:
                    widgets['indicator'].setStatus(Color.ORANGE, status[0])
                else:  # failed
                    widgets['indicator'].setStatus(Color.RED, status[0])

        sequencer_status_v, sequencer_status_t = self.consume_db(
            data, 'obs', 'sequencer_status')
        if sequencer_status_v is not None:
            if sequencer_status_v == SequencerStatus.FOCUSING:
                self.open_focus_window()
                if self.focus_window is not None:
                    self.focus_window.focus_timer.start()

    @Slot(int)
    def on_shutter_combobox_currentIndexChanged(self, index):
        self.action_send(self.shutter_combobox,
                         self.backend.set_plc_shutter_state,
                         self.shutter_combobox.currentData())

    @Slot(bool)
    def on_shutter_init_button_clicked(self, checked):
        self.action_send(self.shutter_init_button,
                         self.backend.get_plc_shutter_init)

    @Slot(int)
    def on_flipmirror_combobox_currentIndexChanged(self, index):
        self.action_send(self.flipmirror_combobox,
                         self.backend.set_plc_flipmirror_position,
                         self.flipmirror_combobox.currentData())

    @Slot(bool)
    def on_flipmirror_init_button_clicked(self, checked):
        self.action_send(self.flipmirror_init_button,
                         self.backend.get_plc_flipmirror_init)

    @Slot(float)
    def on_calibunit_spinbox_valueChanged(self, d):
        self.action_send(self.calibunit_spinbox,
                         self.backend.set_plc_calibunit_position, d)

    @Slot(bool)
    def on_calibunit_init_button_clicked(self, checked):
        self.action_send(self.calibunit_initialize_button,
                         self.backend.get_plc_calibunit_init)

    @Slot(bool)
    def on_calibunit_stop_button_clicked(self, checked):
        self.action_send(self.calibunit_stop_button,
                         self.backend.get_plc_calibunit_stop)

    @Slot(bool)
    def on_calibunit_laser_button_clicked(self, checked):
        self.action_send(self.calibunit_laser_button,
                         self.backend.get_plc_calibunit_laser)

    @Slot(bool)
    def on_calibunit_tungsten_button_clicked(self, checked):
        self.action_send(self.calibunit_tungsten_button,
                         self.backend.get_plc_calibunit_tungsten)

    @Slot(int)
    def on_tungsten_state_checkbox_stateChanged(self, state):
        self.action_send(self.tungsten_state_checkbox,
                         self.backend.set_plc_tungsten_state,
                         Qt.CheckState(state) == Qt.Checked)

    @Slot(bool)
    def on_tungsten_init_button_clicked(self, checked):
        self.action_send(self.tungsten_init_button,
                         self.backend.get_plc_tungsten_init)

    @Slot(int)
    def on_laser_state_checkbox_stateChanged(self, state):
        self.action_send(self.laser_state_checkbox,
                         self.backend.set_plc_laser_state,
                         Qt.CheckState(state) == Qt.Checked)

    @Slot(float)
    def on_laser_power_spinbox_valueChanged(self, d):
        self.action_send(self.laser_power_spinbox,
                         self.backend.set_plc_laser_power, d)

    @Slot(bool)
    def on_laser_init_button_clicked(self, checked):
        self.action_send(self.laser_init_button,
                         self.backend.get_plc_laser_init)

    @Slot(bool)
    def on_lamps_off_button_clicked(self, checked):
        self.action_send(self.lamps_off_button, self.backend.get_plc_lamps_off)

    @Slot(int)
    def on_filterwheel_combobox_currentIndexChanged(self, index):
        self.action_send(self.filterwheel_combobox,
                         self.backend.set_plc_filterwheel_filter,
                         self.filterwheel_combobox.currentData())

    @Slot(bool)
    def on_filterwheel_init_button_clicked(self, checked):
        self.action_send(self.filterwheel_init_button,
                         self.backend.get_plc_filterwheel_init)

    @Slot(float)
    def on_adc1_spinbox_valueChanged(self, d):
        self.action_send(self.adc1_spinbox, self.backend.set_plc_adc_1_angle,
                         d)

    @Slot(bool)
    def on_adc1_init_button_clicked(self, checked):
        self.action_send(self.adc1_init_button, self.backend.get_plc_adc1_init)

    @Slot(bool)
    def on_adc1_stop_button_clicked(self, checked):
        self.action_send(self.adc1_stop_button, self.backend.get_plc_adc1_stop)

    @Slot(float)
    def on_adc2_spinbox_valueChanged(self, d):
        self.action_send(self.adc2_spinbox, self.backend.set_plc_adc_2_angle,
                         d)

    @Slot(bool)
    def on_adc2_init_button_clicked(self, checked):
        self.action_send(self.adc2_init_button, self.backend.get_plc_adc2_init)

    @Slot(bool)
    def on_adc2_stop_button_clicked(self, checked):
        self.action_send(self.adc2_stop_button, self.backend.get_plc_adc2_stop)

    @Slot(bool)
    def on_adc_zero_disp_button_clicked(self, checked):
        self.action_send(self.adc_zero_disp_button,
                         self.backend.get_plc_adc_zerodisp)

    @Slot(bool)
    def on_adc_max_disp_button_clicked(self, checked):
        self.action_send(self.adc_max_disp_button,
                         self.backend.get_plc_adc_maxdisp)

    @Slot(int)
    def on_pump_checkbox_stateChanged(self, state):
        self.action_send(self.pump_checkbox, self.backend.set_plc_pump_state,
                         Qt.CheckState(state) == Qt.Checked)

    @Slot(int)
    def on_fan_checkbox_stateChanged(self, state):
        self.action_send(self.fan_checkbox, self.backend.set_plc_fan_state,
                         Qt.CheckState(state) == Qt.Checked)

    @Slot(int)
    def on_heater_checkbox_stateChanged(self, state):
        self.action_send(self.pump_checkbox, self.backend.set_plc_heater_state,
                         Qt.CheckState(state) == Qt.Checked)

    @Slot(bool)
    def on_fli_new_image_button_clicked(self, checked):
        self.action_send(self.fli_new_image_button, self.backend.set_fli_image,
                         self.fli_exposure_time_spinbox.value(),
                         self.fli_frames_spinbox.value())

    @Slot(bool)
    def on_fli_cancel_button_clicked(self, checked):
        self.action_send(self.fli_cancel_button, self.backend.get_fli_cancel)

    @Slot(bool)
    def on_wfs_acquisition_start_button_clicked(self, checked):
        self.action_send(self.wfs_acquisition_start_button,
                         self.backend.get_nuvu_acquisition_start)

    @Slot(bool)
    def on_wfs_acquisition_stop_button_clicked(self, checked):
        self.action_send(self.wfs_acquisition_start_button,
                         self.backend.get_nuvu_acquisition_stop)

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
            self.dm_channels = DMChannelsWindow(self.backend,
                                                config.AO.DM_loop_number,
                                                parent=self)

    @Slot(bool)
    def on_ttm_channels_button_clicked(self, checked):
        if self.ttm_channels is not None:
            self.ttm_channels.show()
            self.ttm_channels.activateWindow()
        else:
            self.ttm_channels = DMChannelsWindow(self.backend,
                                                 config.AO.TTM_loop_number,
                                                 parent=self)

    @Slot(bool)
    def on_dm_calibration_button_clicked(self, checked):
        if self.dm_calibration is not None:
            self.dm_calibration.show()
            self.dm_calibration.activateWindow()
        else:
            from guis.windows.calibration import CalibrationWindow
            self.dm_calibration = CalibrationWindow(self.backend, 'dm',
                                                    config.AO.DM_loop_number,
                                                    (11, 22), (12, 12),
                                                    parent=self)

    @Slot(bool)
    def on_ttm_calibration_button_clicked(self, checked):
        if self.ttm_calibration is not None:
            self.ttm_calibration.show()
            self.ttm_calibration.activateWindow()
        else:
            from guis.windows.calibration import CalibrationWindow
            self.ttm_calibration = CalibrationWindow(self.backend, 'ttm',
                                                     config.AO.TTM_loop_number,
                                                     (12, 12), (1, 2),
                                                     parent=self)

    @Slot(bool)
    def on_dm_direct_control_button_clicked(self, checked):
        if self.dm_direct_control is not None:
            self.dm_direct_control.show()
            self.dm_direct_control.activateWindow()
        else:
            self.dm_direct_control = DMDirectControlWindow(
                self.backend, parent=self)

    @Slot(bool)
    def on_ttm_direct_control_button_clicked(self, checked):
        if self.ttm_direct_control is not None:
            self.ttm_direct_control.show()
            self.ttm_direct_control.activateWindow()
        else:
            self.ttm_direct_control = TTMDirectControlWindow(
                self.backend, parent=self)

    @Slot(bool)
    def on_centering_star_button_clicked(self, checked):
        self.action_send(self.centering_star_button,
                         self.backend.get_centering_star)

    @Slot(bool)
    def on_centering_laser_button_clicked(self, checked):
        self.action_send(self.centering_laser_button,
                         self.backend.get_centering_laser)

    @Slot(bool)
    def on_open_focus_sequence_button_clicked(self, checked):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setNameFilter('Images (*.fits)')
        dialog.setAcceptMode(QFileDialog.AcceptOpen)

        error_dialog = KMessageBox(self)
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setModal(False)
        error_dialog.setText("<b>Focus sequence loading failed!</b>")

        try:
            if dialog.exec():
                filenames = dialog.selectedFiles()

                if len(filenames) != 1:
                    error_dialog.setInformativeText(
                        f'Select one and only one file (got {len(filenames)}).'
                    )
                    error_dialog.show()
                    return

                filename = Path(filenames[0])

                if not filename.exists():
                    error_dialog.setInformativeText('File does not exists.')
                    error_dialog.show()
                    return

                if filename.suffix.lower() != '.fits':
                    error_dialog.setInformativeText(
                        f'Unsupported file extension "{filename.suffix}".')
                    error_dialog.show()

                FocusWindow(self.backend, filename, parent=self)
        except PermissionError:
            error_dialog.setInformativeText(
                'Can\'t read file, permission refused.')
            error_dialog.show()

    @Slot(bool)
    def on_focusing_sequence_button_clicked(self, checked):
        self.action_send(self.focusing_sequence_button,
                         self.backend.get_focus_sequence)

    @Slot(bool)
    def on_focusing_autofocus_button_clicked(self, checked):
        self.action_send(self.focusing_autofocus_button,
                         self.backend.get_focus_autofocus)

    def on_service_action_button_clicked(self, checked, unit, action):
        self.action_send([], self.backend.set_services_action, unit, action)

    def open_focus_window(self):
        if self.focus_window is not None:
            self.focus_window.show()
            self.focus_window.activateWindow()
        else:
            self.focus_window = FocusWindow(self.backend, parent=self)

    def eventFilter(self, source, event):
        if hasattr(source, 'hover_text'):
            if event.type() == QEvent.Enter:
                self.hovered.emit(source.hover_text)
            elif event.type() == QEvent.Leave:
                self.hovered.emit('')
        return QObject.eventFilter(self, source, event)
