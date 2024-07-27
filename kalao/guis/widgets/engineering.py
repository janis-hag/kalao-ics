import functools
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

from PySide6.QtCore import (QEvent, QObject, QSignalBlocker, QTimer, Signal,
                            Slot)
from PySide6.QtGui import Qt
from PySide6.QtWidgets import (QFileDialog, QFrame, QLabel, QLineEdit,
                               QMessageBox, QPushButton, QSizePolicy)

from kalao.guis.utils.definitions import Color
from kalao.guis.utils.mixins import BackendActionMixin, BackendDataMixin
from kalao.guis.utils.ui_loader import loadUi, setEnabledStack
from kalao.guis.utils.widgets import (KLabel, KMessageBox, KStatusIndicator,
                                      KWidget)
from kalao.guis.windows.ao_calibration import AOCalibrationWindow
from kalao.guis.windows.calibration_poses import CalibrationPosesWindow
from kalao.guis.windows.dm_channels import DMChannelsWindow
from kalao.guis.windows.dm_direct_control import DMDirectControlWindow
from kalao.guis.windows.focus_sequence import FocusSequenceWindow
from kalao.guis.windows.ttm_direct_control import TTMDirectControlWindow

from kalao.definitions.enums import (CameraServerStatus, CameraStatus,
                                     FilterWheelStatus, FlipMirrorStatus,
                                     IPPowerStatus, LaserStatus, PLCStatus,
                                     RelayState, SequencerStatus,
                                     ServiceAction, ShutterStatus,
                                     TungstenStatus)

import config


class EngineeringWidget(KWidget, BackendActionMixin, BackendDataMixin):
    hovered = Signal(str)
    updated = Signal(int, int)

    activeToolTip = None

    dm_channels_window = None
    ttm_channels_window = None
    dm_calibration_window = None
    ttm_calibration_window = None
    dm_direct_control_window = None
    ttm_direct_control_window = None
    focus_sequence_window = None
    calibration_poses_window = None

    def __init__(self, backend, deadman=False, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.backend = backend

        loadUi('engineering.ui', self)
        self.resize(600, 400)

        self.indicators_list = []

        for key in dir(self):
            attr = getattr(self, key)

            if isinstance(attr, KStatusIndicator):
                attr.installEventFilter(self)
                self.indicators_list.append(attr)

        with QSignalBlocker(self.shutter_combobox):
            for status in [ShutterStatus.CLOSED, ShutterStatus.OPEN]:
                self.shutter_combobox.addItem(status, status)

            self.shutter_combobox.setCurrentIndex(-1)

        with QSignalBlocker(self.flipmirror_combobox):
            for position in [FlipMirrorStatus.DOWN, FlipMirrorStatus.UP]:
                self.flipmirror_combobox.addItem(position, position)

            self.flipmirror_combobox.setCurrentIndex(-1)

        with QSignalBlocker(self.filterwheel_combobox):
            for filter in config.FilterWheel.position_list:
                self.filterwheel_combobox.addItem(
                    self.filter_display_name(filter), filter)

            self.filterwheel_combobox.setCurrentIndex(-1)

        # Warning: always put init button first! (used by _hardware_update_enabled function)
        self.shutter_widgets = [
            self.shutter_init_button, self.shutter_combobox
        ]
        self.flipmirror_widgets = [
            self.flipmirror_init_button, self.flipmirror_combobox
        ]
        self.calibunit_widgets = [
            self.calibunit_init_button, self.calibunit_spinbox,
            self.calibunit_laser_button, self.calibunit_tungsten_button
        ]
        self.tungsten_widgets = [
            self.tungsten_init_button, self.tungsten_status_checkbox
        ]
        self.laser_widgets = [
            self.laser_init_button, self.laser_status_checkbox,
            self.laser_power_spinbox
        ]
        self.filterwheel_widgets = [
            self.filterwheel_init_button, self.filterwheel_combobox
        ]
        self.adc1_widgets = [self.adc1_init_button, self.adc1_spinbox]
        self.adc2_widgets = [self.adc2_init_button, self.adc2_spinbox]
        self.adc_widgets = [
            self.adc_angle_spinbox, self.adc_offset_spinbox,
            self.adc_zero_disp_button, self.adc_max_disp_button
        ]
        self.camera_widgets = [
            self.camera_exposure_time_spinbox, self.camera_frames_spinbox,
            self.camera_roi_spinbox, self.camera_new_image_button
        ]
        self.centering_widgets = [
            self.centering_star_button, self.centering_laser_button,
            self.centering_spiral_search_button
        ]

        ##### Services

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
            self.indicators_list.append(indicator)

            unit = service['unit']

            self.services_widgets[unit] = {
                'lineedit': lineedit,
                'indicator': indicator,
                'buttons': {},
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

                button._disable_stack = []
                button.setEnabledStack = functools.partial(
                    setEnabledStack, button)

                button.clicked.connect(
                    lambda checked=False, unit=unit, action=action: self.
                    on_service_action_button_clicked(checked, unit, action))
                self.services_layout.addWidget(button, i, 3 + j)

                if action == ServiceAction.RELOAD and not service.get(
                        'reload-allowed', False) or service.get(
                            'system', False):
                    button.setEnabledStack(False, 'config')
                else:
                    self.services_widgets[unit]['buttons'][action] = button

        self.services_layout.setColumnStretch(0, 0)
        self.services_layout.setColumnStretch(1, 0)
        self.services_layout.setColumnStretch(2, 2)
        self.services_layout.setColumnStretch(3, 1)
        self.services_layout.setColumnStretch(4, 1)
        self.services_layout.setColumnStretch(5, 1)
        self.services_layout.setColumnStretch(6, 1)
        self.services_layout.setColumnStretch(7, 1)

        ##### CACAO processes

        self.milk_processes_widgets = {}
        for i, proc in enumerate(config.AO.processes):
            if proc is None:
                frame = QFrame()
                frame.setFrameShape(QFrame.HLine)
                frame.setFrameShadow(QFrame.Sunken)

                row = i + 1

                self.proc_layout.addWidget(frame, row, 0, 1, 4)
            else:
                label = QLabel(proc)

                tmux_indicator = KStatusIndicator()
                tmux_indicator.setCursor(Qt.WhatsThisCursor)
                tmux_indicator.installEventFilter(self)
                tmux_indicator.setFixedSize(20, 20)
                tmux_indicator.setSizePolicy(QSizePolicy.Fixed,
                                             QSizePolicy.Fixed)
                self.indicators_list.append(tmux_indicator)

                conf_indicator = KStatusIndicator()
                conf_indicator.setCursor(Qt.WhatsThisCursor)
                conf_indicator.installEventFilter(self)
                conf_indicator.setFixedSize(20, 20)
                conf_indicator.setSizePolicy(QSizePolicy.Fixed,
                                             QSizePolicy.Fixed)
                self.indicators_list.append(conf_indicator)

                run_indicator = KStatusIndicator()
                run_indicator.setCursor(Qt.WhatsThisCursor)
                run_indicator.installEventFilter(self)
                run_indicator.setFixedSize(20, 20)
                run_indicator.setSizePolicy(QSizePolicy.Fixed,
                                            QSizePolicy.Fixed)
                self.indicators_list.append(run_indicator)

                row = i + 1

                self.proc_layout.addWidget(label, row, 0, Qt.AlignLeft)
                self.proc_layout.addWidget(tmux_indicator, row, 1,
                                           Qt.AlignHCenter)
                self.proc_layout.addWidget(conf_indicator, row, 2,
                                           Qt.AlignHCenter)
                self.proc_layout.addWidget(run_indicator, row, 3,
                                           Qt.AlignHCenter)

                self.milk_processes_widgets[proc] = {
                    'tmux_indicator': tmux_indicator,
                    'conf_indicator': conf_indicator,
                    'run_indicator': run_indicator,
                }

        ##### CACAO streams

        self.milk_streams_widgets = {}
        self.milk_streams_md = {}
        for i, stream in enumerate(config.AO.streams):
            if stream is None:
                frame = QFrame()
                frame.setFrameShape(QFrame.HLine)
                frame.setFrameShadow(QFrame.Sunken)

                row = i + 1

                self.stream_layout.addWidget(frame, row, 0, 1, 4)
            else:
                label = QLabel(stream)

                indicator = KStatusIndicator()
                indicator.setCursor(Qt.WhatsThisCursor)
                indicator.installEventFilter(self)
                indicator.setFixedSize(20, 20)
                indicator.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
                self.indicators_list.append(indicator)

                size_label = QLabel('Unknown')
                fps_label = KLabel('{fps:.1f} Hz')
                fps_label.updateText(fps=np.nan)

                row = i + 1

                self.stream_layout.addWidget(label, row, 0, Qt.AlignLeft)
                self.stream_layout.addWidget(indicator, row, 1,
                                             Qt.AlignHCenter)
                self.stream_layout.addWidget(size_label, row, 2,
                                             Qt.AlignHCenter)
                self.stream_layout.addWidget(fps_label, row, 3, Qt.AlignRight)

                self.milk_streams_widgets[stream] = {
                    'indicator': indicator,
                    'size_label': size_label,
                    'fps_label': fps_label,
                }

        ##### Dead-man

        self.deadman_timer = QTimer()
        self.deadman_timer.setInterval(
            int(1000 * config.Hardware.inactivity_timeout / 3))
        self.deadman_timer.timeout.connect(self.update_deadman)
        self.reset_deadman()

        self.deadman_checkbox.setChecked(deadman)

        ##### Misc.

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
        ##### PLC / Misc. Hardware

        # Shutter

        shutter_status = self.consume_dict(data, 'hw', 'shutter_status')
        if shutter_status is not None:
            with QSignalBlocker(self.shutter_combobox):
                self.shutter_combobox.setCurrentIndex(
                    self.shutter_combobox.findData(shutter_status))

            enabled = True
            init_enabled = True

            if shutter_status == ShutterStatus.OPEN:
                self.shutter_indicator.setStatus(Color.GREEN,
                                                 shutter_status.name)
            elif shutter_status == ShutterStatus.CLOSED:
                self.shutter_indicator.setStatus(Color.BLACK,
                                                 shutter_status.name)
            else:  # ERROR
                self.shutter_indicator.setStatus(Color.RED,
                                                 shutter_status.name)
                enabled = False

            self._hardware_update_enabled(self.shutter_widgets, enabled,
                                          init_enabled, 'shutter_status')

        # Flip Mirror

        flipmirror_status = self.consume_dict(data, 'hw', 'flipmirror_status')
        if flipmirror_status is not None:
            with QSignalBlocker(self.flipmirror_combobox):
                self.flipmirror_combobox.setCurrentIndex(
                    self.flipmirror_combobox.findData(flipmirror_status))

            enabled = True
            init_enabled = True

            if flipmirror_status == FlipMirrorStatus.DOWN:
                self.flipmirror_indicator.setStatus(Color.BLACK,
                                                    flipmirror_status.name)
            elif flipmirror_status == FlipMirrorStatus.UP:
                self.flipmirror_indicator.setStatus(Color.YELLOW,
                                                    flipmirror_status.name)
            elif flipmirror_status == FlipMirrorStatus.UNKNOWN:
                self.flipmirror_indicator.setStatus(Color.BLUE,
                                                    flipmirror_status.name)
            else:  # ERROR
                self.flipmirror_indicator.setStatus(Color.RED,
                                                    flipmirror_status.name)
                enabled = False

            self._hardware_update_enabled(self.flipmirror_widgets, enabled,
                                          init_enabled, 'flipmirror_status')

        # Calibration Unit

        calibunit_position = self.consume_dict(data, 'hw',
                                               'calibunit_position')
        if calibunit_position is not None:
            with QSignalBlocker(self.calibunit_spinbox):
                self.calibunit_spinbox.setValue(calibunit_position)

        calibunit_status = self.consume_dict(data, 'hw', 'calibunit_status')
        if calibunit_status is not None:
            enabled = False
            init_enabled = False

            if calibunit_status == PLCStatus.STANDING:
                self.calibunit_indicator.setStatus(Color.GREEN,
                                                   calibunit_status.name)
                enabled = True
                init_enabled = True
            elif calibunit_status == PLCStatus.MOVING:
                self.calibunit_indicator.setStatus(Color.BLUE,
                                                   calibunit_status.name)
            elif calibunit_status == PLCStatus.INITIALISING:
                self.calibunit_indicator.setStatus(Color.ORANGE,
                                                   calibunit_status.name)

            else:  # NOT_ENABLED, NOT_INITIALISED, ERROR, UNKNOWN
                self.calibunit_indicator.setStatus(Color.RED,
                                                   calibunit_status.name)
                init_enabled = True

            self._hardware_update_enabled(self.calibunit_widgets, enabled,
                                          init_enabled, 'calibunit_status')

        # Tungsten

        tungsten_status = self.consume_dict(data, 'hw', 'tungsten_status')
        if tungsten_status is not None:
            with QSignalBlocker(self.tungsten_status_checkbox):
                self.tungsten_status_checkbox.setChecked(
                    tungsten_status == TungstenStatus.ON)

            enabled = True
            init_enabled = True

            if tungsten_status == TungstenStatus.ON:
                self.tungsten_status_indicator.setStatus(
                    Color.YELLOW, tungsten_status.name)
            elif tungsten_status == TungstenStatus.OFF:
                self.tungsten_status_indicator.setStatus(
                    Color.BLACK, tungsten_status.name)
            else:  # ERROR
                self.tungsten_status_indicator.setStatus(
                    Color.RED, tungsten_status.name)
                enabled = False

            self._hardware_update_enabled(self.tungsten_widgets, enabled,
                                          init_enabled, 'tungsten_status')

        # Laser

        laser_status = self.consume_dict(data, 'hw', 'laser_status')
        if laser_status is not None:
            with QSignalBlocker(self.laser_status_checkbox):
                self.laser_status_checkbox.setChecked(
                    laser_status == LaserStatus.ON)

        laser_power = self.consume_dict(data, 'hw', 'laser_power')
        if laser_power is not None:
            with QSignalBlocker(self.laser_power_spinbox):
                self.laser_power_spinbox.setValue(laser_power)

        if laser_power is not None or laser_status is not None:
            laser_status = self.consume_dict(data, 'hw', 'laser_status',
                                             force=True)
            laser_power = self.consume_dict(data, 'hw', 'laser_power',
                                            force=True)

            enabled = True
            init_enabled = True

            if laser_status == LaserStatus.ON and laser_power > 0:
                self.laser_indicator.setStatus(
                    Color.YELLOW, f'{laser_status.name} & {laser_power}')
            elif laser_status == LaserStatus.OFF or laser_power == 0:
                self.laser_indicator.setStatus(
                    Color.BLACK, f'{laser_status.name} & {laser_power}')
            else:  # ERROR or < 0
                self.laser_indicator.setStatus(
                    Color.RED, f'{laser_status.name} & {laser_power}')
                enabled = False

            self._hardware_update_enabled(self.laser_widgets, enabled,
                                          init_enabled,
                                          'laser_status_and_power')

        # Filter Wheel

        filterwheel_filter_name = self.consume_dict(data, 'hw',
                                                    'filterwheel_filter_name')
        if filterwheel_filter_name is not None:
            with QSignalBlocker(self.filterwheel_combobox):
                self.filterwheel_combobox.setCurrentIndex(
                    self.filterwheel_combobox.findData(
                        filterwheel_filter_name))

            enabled = True
            init_enabled = True

            if filterwheel_filter_name != FilterWheelStatus.ERROR_NAME:
                self.filterwheel_indicator.setStatus(Color.GREEN,
                                                     filterwheel_filter_name)
            else:  # ERROR
                self.filterwheel_indicator.setStatus(Color.RED,
                                                     filterwheel_filter_name)
                enabled = False

            self._hardware_update_enabled(self.laser_widgets, enabled,
                                          init_enabled,
                                          'filterwheel_filter_name')

        # ADC

        adc1_angle = self.consume_dict(data, 'hw', 'adc1_angle')
        if adc1_angle is not None:
            with QSignalBlocker(self.adc1_spinbox):
                self.adc1_spinbox.setValue(adc1_angle)

        adc1_status = self.consume_dict(data, 'hw', 'adc1_status')
        if adc1_status is not None:
            enabled = False
            init_enabled = False

            if adc1_status == PLCStatus.STANDING:
                self.adc1_indicator.setStatus(Color.GREEN, adc1_status.name)
                enabled = True
                init_enabled = True
            elif adc1_status == PLCStatus.MOVING:
                self.adc1_indicator.setStatus(Color.BLUE, adc1_status.name)
            elif adc1_status == PLCStatus.INITIALISING:
                self.adc1_indicator.setStatus(Color.ORANGE, adc1_status.name)
            else:  # NOT_ENABLED, NOT_INITIALISED, ERROR, UNKNOWN
                self.adc1_indicator.setStatus(Color.RED, adc1_status.name)
                init_enabled = True

            self._hardware_update_enabled(self.adc1_widgets + self.adc_widgets,
                                          enabled, init_enabled, 'adc1_status')

        adc2_angle = self.consume_dict(data, 'hw', 'adc2_angle')
        if adc2_angle is not None:
            with QSignalBlocker(self.adc2_spinbox):
                self.adc2_spinbox.setValue(adc2_angle)

        adc2_status = self.consume_dict(data, 'hw', 'adc2_status')
        if adc2_status is not None:
            enabled = False
            init_enabled = False

            if adc2_status == PLCStatus.STANDING:
                self.adc2_indicator.setStatus(Color.GREEN, adc2_status.name)
                enabled = True
                init_enabled = True
            elif adc2_status == PLCStatus.MOVING:
                self.adc2_indicator.setStatus(Color.BLUE, adc2_status.name)
            elif adc2_status == PLCStatus.INITIALISING:
                self.adc2_indicator.setStatus(Color.ORANGE, adc2_status.name)
            else:  # NOT_ENABLED, NOT_INITIALISED, ERROR, UNKNOWN
                self.adc2_indicator.setStatus(Color.RED, adc2_status.name)
                init_enabled = True

            self._hardware_update_enabled(self.adc2_widgets + self.adc_widgets,
                                          enabled, init_enabled, 'adc2_status')

        adc_angle = self.consume_dict(data, 'hw', 'adc_angle')
        if adc_angle is not None:
            with QSignalBlocker(self.adc_angle_spinbox):
                self.adc_angle_spinbox.setValue(adc_angle)

        adc_offset = self.consume_dict(data, 'hw', 'adc_offset')
        if adc_offset is not None:
            with QSignalBlocker(self.adc_offset_spinbox):
                self.adc_offset_spinbox.setValue(adc_offset)

        # Cooling system

        pump_status = self.consume_dict(data, 'hw', 'pump_status')
        if pump_status is not None:
            with QSignalBlocker(self.pump_checkbox):
                self.pump_checkbox.setChecked(pump_status == RelayState.ON)

            if pump_status == RelayState.ON:
                self.pump_indicator.setStatus(Color.GREEN, pump_status.name)
            elif pump_status == RelayState.OFF:
                self.pump_indicator.setStatus(Color.BLACK, pump_status.name)
            else:
                self.pump_indicator.setStatus(Color.RED, pump_status.name)

        heatexchanger_fan_status = self.consume_dict(
            data, 'hw', 'heatexchanger_fan_status')
        if heatexchanger_fan_status is not None:
            with QSignalBlocker(self.heatexchanger_fan_checkbox):
                self.heatexchanger_fan_checkbox.setChecked(
                    heatexchanger_fan_status == RelayState.ON)

            if heatexchanger_fan_status == RelayState.ON:
                self.heatexchanger_fan_indicator.setStatus(
                    Color.GREEN, heatexchanger_fan_status.name)
            elif heatexchanger_fan_status == RelayState.OFF:
                self.heatexchanger_fan_indicator.setStatus(
                    Color.BLACK, heatexchanger_fan_status.name)
            else:
                self.heatexchanger_fan_indicator.setStatus(
                    Color.RED, heatexchanger_fan_status.name)

        heater_status = self.consume_dict(data, 'hw', 'heater_status')
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

        ##### IPPower

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

        ##### Science Camera

        exposure_time = self.consume_dict(data, 'camera', 'exposure_time')
        if exposure_time is not None:
            with QSignalBlocker(self.camera_exposure_time_spinbox):
                self.camera_exposure_time_spinbox.setValue(exposure_time)

        remaining_time = self.consume_dict(data, 'camera', 'remaining_time')
        if remaining_time is not None:
            with QSignalBlocker(self.camera_remaining_time_spinbox):
                self.camera_remaining_time_spinbox.setValue(remaining_time)

        frames = self.consume_dict(data, 'camera', 'frames')
        if frames is not None:
            with QSignalBlocker(self.camera_frames_spinbox):
                self.camera_frames_spinbox.setValue(frames)

        remaining_frames = self.consume_dict(data, 'camera',
                                             'remaining_frames')
        if remaining_frames is not None:
            with QSignalBlocker(self.camera_remaining_frames_spinbox):
                self.camera_remaining_frames_spinbox.setValue(remaining_frames)

        camera_server_status = self.consume_dict(data, 'camera',
                                                 'camera_server_status')
        if camera_server_status is not None:
            if camera_server_status == CameraServerStatus.UP:
                self.camera_server_status_indicator.setStatus(
                    Color.GREEN, camera_server_status)
            elif camera_server_status == CameraServerStatus.DOWN:
                self.camera_server_status_indicator.setStatus(
                    Color.BLACK, camera_server_status)
            else:
                self.camera_server_status_indicator.setStatus(
                    Color.RED, camera_server_status)

        camera_status = self.consume_dict(data, 'camera', 'camera_status')
        if camera_status is not None:
            if camera_status in [
                    CameraStatus.EXPOSING, CameraStatus.READING_CCD
            ]:
                self.camera_status_indicator.setStatus(Color.GREEN,
                                                       camera_status)
            elif camera_status in [
                    CameraStatus.IDLE, CameraStatus.WAITING_TRIGGER
            ]:
                self.camera_status_indicator.setStatus(Color.BLACK,
                                                       camera_status)
            else:  # UNKNOWN, ERROR
                self.camera_status_indicator.setStatus(Color.RED,
                                                       camera_status)

            self.camera_status_lineedit.setText(camera_status)

            enabled = camera_status in [
                CameraStatus.IDLE, CameraStatus.WAITING_TRIGGER
            ]
            for widget in self.camera_widgets:
                widget.setEnabledStack(enabled, 'camera_status')

        ##### Wavefront Sensor

        maqtime = self.consume_shm_keyword(data, config.SHM.NUVU_RAW,
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

        ##### Services

        for i, service in enumerate(config.Systemd.services.values()):
            status = self.consume_dict(data, 'services', service['unit'])
            if status is not None:
                widgets = self.services_widgets[service['unit']]
                widgets['lineedit'].setText(f'{status[0]}')
                if status[1] != '':
                    detailed_status = f'{status[0]} ({status[1]})'
                else:
                    detailed_status = f'{status[0]}'
                widgets['lineedit'].setToolTip(
                    f'Status: {detailed_status} | Since: {status[2].astimezone():%H:%M:%S %d-%m-%Y}'
                )

                buttons_enabled = True
                if status[0] == 'active':
                    widgets['indicator'].setStatus(Color.GREEN, status[0])
                elif status[0] == 'inactive':
                    widgets['indicator'].setStatus(Color.BLACK, status[0])
                elif status[0] in ['activating', 'deactivating', 'reloading']:
                    widgets['indicator'].setStatus(Color.ORANGE, status[0])
                    buttons_enabled = False
                else:  # failed
                    widgets['indicator'].setStatus(Color.RED, status[0])

                for key, button in widgets['buttons'].items():
                    if key != ServiceAction.KILL:
                        button.setEnabledStack(buttons_enabled,
                                               'service_status')

        ##### Sequencer status (automatic windows opening)

        sequencer_status = self.consume_dict(data, 'memory',
                                             'sequencer_status')
        if sequencer_status is not None:
            if sequencer_status == SequencerStatus.FOCUSING:
                # Note: force timer start in case the window was not closed
                self.open_focus_sequence_window(force_timer=True)

            elif sequencer_status == SequencerStatus.CALIBRATIONS:
                self.open_calibration_poses_window()

        ##### CACAO / camstack

        tmux_sessions = self.consume_dict(data, 'tmux', 'tmux_sessions')
        if tmux_sessions is not None:
            if 'kalaocam_ctrl' in tmux_sessions:
                self.kalaocamctrl_tmux_indicator.setStatus(Color.GREEN)
            else:
                self.kalaocamctrl_tmux_indicator.setStatus(Color.BLACK)

            if 'nuvu_fgrab' in tmux_sessions:
                self.nuvufgrab_tmux_indicator.setStatus(Color.GREEN)
            else:
                self.nuvufgrab_tmux_indicator.setStatus(Color.BLACK)

            for proc in config.AO.processes:
                if proc is None:
                    continue

                if proc in tmux_sessions:
                    self.milk_processes_widgets[proc][
                        'tmux_indicator'].setStatus(Color.GREEN)
                else:
                    self.milk_processes_widgets[proc][
                        'tmux_indicator'].setStatus(Color.BLACK)

        kalaocam_ctrl_proc = self.consume_dict(data, 'pgrep', 'kalaocam_ctrl')
        if kalaocam_ctrl_proc is not None:
            if kalaocam_ctrl_proc == 0:
                self.kalaocamctrl_proc_indicator.setStatus(
                    Color.GREEN, kalaocam_ctrl_proc)
            else:
                self.kalaocamctrl_proc_indicator.setStatus(
                    Color.BLACK, kalaocam_ctrl_proc)

        nuvu_fgrab_proc = self.consume_dict(data, 'pgrep', 'nuvu_fgrab')
        if nuvu_fgrab_proc is not None:
            if nuvu_fgrab_proc == 0:
                self.nuvufgrab_proc_indicator.setStatus(
                    Color.GREEN, nuvu_fgrab_proc)
            else:
                self.nuvufgrab_proc_indicator.setStatus(
                    Color.BLACK, nuvu_fgrab_proc)

        for proc in config.AO.processes:
            if proc is None:
                continue

            status = self.consume_fps_status(data, proc)

            if status is not None:
                if 'C' in status:
                    self.milk_processes_widgets[proc][
                        'conf_indicator'].setStatus(Color.GREEN, status)
                else:
                    self.milk_processes_widgets[proc][
                        'conf_indicator'].setStatus(Color.BLACK, status)

                if 'R' in status:
                    self.milk_processes_widgets[proc][
                        'run_indicator'].setStatus(Color.GREEN, status)
                else:
                    self.milk_processes_widgets[proc][
                        'run_indicator'].setStatus(Color.BLACK, status)

        for stream in config.AO.streams:
            if stream is None:
                continue

            status = self.consume_shm_status(data, stream)
            if status is not None:
                if 'E' in status:
                    self.milk_streams_widgets[stream]['indicator'].setStatus(
                        Color.GREEN, status)
                else:
                    self.milk_streams_widgets[stream]['indicator'].setStatus(
                        Color.BLACK, status)

            md = self.consume_shm_md(data, stream, force=True)
            if md is not None:
                if stream in self.milk_streams_md:
                    previous_md = self.milk_streams_md[stream]

                    delta_cnt = md['cnt0'] - previous_md['cnt0']
                    delta_acqtime = (md['acqtime'] -
                                     previous_md['acqtime']).total_seconds()

                    if previous_md['creationtime'] != md['creationtime']:
                        fps = np.nan
                    elif delta_cnt == 0:
                        fps = 0
                    elif delta_cnt < 0 or delta_acqtime == 0:
                        fps = np.nan
                    else:
                        fps = delta_cnt / delta_acqtime
                else:
                    fps = np.nan

                shape = md['shape']
                if len(shape) == 1:
                    shape = (shape[0], 1)

                self.milk_streams_md[stream] = md.copy()
                self.milk_streams_widgets[stream]['fps_label'].updateText(
                    fps=fps)
                self.milk_streams_widgets[stream]['size_label'].setText(
                    'x'.join([str(i) for i in shape]))

        ##### Indicators

        warnings = 0
        errors = 0
        for indicator in self.indicators_list:
            if indicator.brush.color() == Color.ORANGE:
                warnings += 1
            elif indicator.brush.color() == Color.RED:
                errors += 1
        self.updated.emit(warnings, errors)

    def _hardware_update_enabled(self, widgets, enabled, init_enabled, source):
        for i, widget in enumerate(widgets):
            if i == 0:
                widget.setEnabledStack(init_enabled, source)
            else:
                widget.setEnabledStack(enabled, source)

    @Slot(int)
    def on_shutter_combobox_currentIndexChanged(self, index):
        self.action_send(self.shutter_widgets,
                         self.backend.hardware_shutter_status,
                         status=self.shutter_combobox.currentData())

    @Slot(bool)
    def on_shutter_init_button_clicked(self, checked):
        self.action_send(self.shutter_widgets,
                         self.backend.hardware_shutter_init)

    @Slot(int)
    def on_flipmirror_combobox_currentIndexChanged(self, index):
        self.action_send(self.flipmirror_widgets,
                         self.backend.hardware_flipmirror_status,
                         status=self.flipmirror_combobox.currentData())

    @Slot(bool)
    def on_flipmirror_init_button_clicked(self, checked):
        self.action_send(self.flipmirror_widgets,
                         self.backend.hardware_flipmirror_init)

    @Slot(float)
    def on_calibunit_spinbox_valueChanged(self, d):
        self.action_send(self.calibunit_widgets,
                         self.backend.hardware_calibunit_position, position=d)

    @Slot(bool)
    def on_calibunit_init_button_clicked(self, checked):
        self.action_send(self.calibunit_widgets,
                         self.backend.hardware_calibunit_init)

    @Slot(bool)
    def on_calibunit_stop_button_clicked(self, checked):
        self.action_send(self.calibunit_widgets + [self.calibunit_stop_button],
                         self.backend.hardware_calibunit_stop)

    @Slot(bool)
    def on_calibunit_laser_button_clicked(self, checked):
        self.action_send(self.calibunit_widgets,
                         self.backend.hardware_calibunit_laser)

    @Slot(bool)
    def on_calibunit_tungsten_button_clicked(self, checked):
        self.action_send(self.calibunit_widgets,
                         self.backend.hardware_calibunit_tungsten)

    @Slot(int)
    def on_tungsten_status_checkbox_stateChanged(self, state):
        self.action_send(self.tungsten_widgets,
                         self.backend.hardware_tungsten_status,
                         status=Qt.CheckState(state) == Qt.Checked)

    @Slot(bool)
    def on_tungsten_init_button_clicked(self, checked):
        self.action_send(self.tungsten_widgets,
                         self.backend.hardware_tungsten_init)

    @Slot(int)
    def on_laser_status_checkbox_stateChanged(self, state):
        self.action_send([self.laser_status_checkbox, self.laser_init_button],
                         self.backend.hardware_laser_status,
                         status=Qt.CheckState(state) == Qt.Checked)

    @Slot(float)
    def on_laser_power_spinbox_valueChanged(self, d):
        self.action_send([self.laser_power_spinbox, self.laser_init_button],
                         self.backend.hardware_laser_power, power=d)

    @Slot(bool)
    def on_laser_init_button_clicked(self, checked):
        self.action_send(self.laser_widgets, self.backend.hardware_laser_init)

    @Slot(bool)
    def on_lamps_off_button_clicked(self, checked):
        self.action_send(self.tungsten_widgets + self.laser_widgets,
                         self.backend.hardware_lamps_off)

    @Slot(int)
    def on_filterwheel_combobox_currentIndexChanged(self, index):
        self.action_send(self.filterwheel_widgets,
                         self.backend.hardware_filterwheel_filter,
                         filter=self.filterwheel_combobox.currentData())

    @Slot(bool)
    def on_filterwheel_init_button_clicked(self, checked):
        self.action_send(self.filterwheel_widgets,
                         self.backend.hardware_filterwheel_init)

    @Slot(float)
    def on_adc1_spinbox_valueChanged(self, d):
        self.action_send(self.adc1_widgets + self.adc_widgets,
                         self.backend.hardware_adc1_angle, position=d)

    @Slot(bool)
    def on_adc1_init_button_clicked(self, checked):
        self.action_send(self.adc1_widgets + self.adc_widgets,
                         self.backend.hardware_adc1_init)

    @Slot(bool)
    def on_adc1_stop_button_clicked(self, checked):
        self.action_send(
            self.adc1_widgets + self.adc_widgets + [self.adc1_stop_button],
            self.backend.hardware_adc1_stop)

    @Slot(float)
    def on_adc2_spinbox_valueChanged(self, d):
        self.action_send(self.adc2_widgets + self.adc_widgets,
                         self.backend.hardware_adc2_angle, position=d)

    @Slot(bool)
    def on_adc2_init_button_clicked(self, checked):
        self.action_send(self.adc2_widgets + self.adc_widgets,
                         self.backend.hardware_adc2_init)

    @Slot(bool)
    def on_adc2_stop_button_clicked(self, checked):
        self.action_send(
            self.self.adc2_widgets + self.adc_widgets +
            [self.adc2_stop_button], self.backend.hardware_adc2_stop)

    @Slot(bool)
    def on_adc_zero_disp_button_clicked(self, checked):
        self.action_send(
            self.adc1_widgets + self.adc2_widgets + self.adc_widgets,
            self.backend.hardware_adc_zerodisp)

    @Slot(bool)
    def on_adc_max_disp_button_clicked(self, checked):
        self.action_send(
            self.adc1_widgets + self.adc2_widgets + self.adc_widgets,
            self.backend.hardware_adc_maxdisp)

    @Slot(float)
    def on_adc_angle_spinbox_valueChanged(self, d):
        self.action_send(
            self.adc1_widgets + self.adc2_widgets + self.adc_widgets,
            self.backend.hardware_adc_angleoffset, angle=d,
            offset=self.adc_offset_spinbox.value())

    @Slot(float)
    def on_adc_offset_spinbox_valueChanged(self, d):
        self.action_send(
            self.adc1_widgets + self.adc2_widgets + self.adc_widgets,
            self.backend.hardware_adc_angleoffset, offset=d,
            angle=self.adc_angle_spinbox.value())

    @Slot(int)
    def on_pump_checkbox_stateChanged(self, state):
        self.action_send(self.pump_checkbox, self.backend.hardware_pump_status,
                         state=Qt.CheckState(state) == Qt.Checked)

    @Slot(int)
    def on_heatexchanger_fan_checkbox_stateChanged(self, state):
        self.action_send(self.heatexchanger_fan_checkbox,
                         self.backend.hardware_fan_status,
                         state=Qt.CheckState(state) == Qt.Checked)

    @Slot(int)
    def on_heater_checkbox_stateChanged(self, state):
        self.action_send(self.pump_checkbox,
                         self.backend.hardware_heater_status,
                         state=Qt.CheckState(state) == Qt.Checked)

    @Slot(float)
    def on_camera_exposure_time_spinbox_valueChanged(self, d):
        self.action_send(self.camera_exposure_time_spinbox,
                         self.backend.camera_exptime, exposure_time=d)

    @Slot(bool)
    def on_camera_new_image_button_clicked(self, checked):
        self.action_send(
            self.camera_widgets, self.backend.camera_take,
            exposure_time=self.camera_exposure_time_spinbox.value(),
            frames=self.camera_frames_spinbox.value(),
            roi_size=self.camera_roi_spinbox.value())

    @Slot(bool)
    def on_camera_cancel_button_clicked(self, checked):
        self.action_send(self.camera_widgets + [self.camera_cancel_button],
                         self.backend.camera_cancel)

    @Slot(bool)
    def on_wfs_acquisition_start_button_clicked(self, checked):
        self.action_send([
            self.wfs_acquisition_start_button, self.wfs_acquisition_stop_button
        ], self.backend.wfs_acquisition_start)

    @Slot(bool)
    def on_wfs_acquisition_stop_button_clicked(self, checked):
        self.action_send([
            self.wfs_acquisition_stop_button, self.wfs_acquisition_start_button
        ], self.backend.wfs_acquisition_stop)

    @Slot(bool)
    def on_ippower_rtc_on_button_clicked(self, checked):
        self.action_send([
            self.ippower_rtc_on_button, self.ippower_rtc_off_button
        ], self.backend.ippower_rtc_on)

    @Slot(bool)
    def on_ippower_rtc_off_button_clicked(self, checked):
        self.action_send([
            self.ippower_rtc_off_button, self.ippower_rtc_on_button
        ], self.backend.ippower_rtc_off)

    @Slot(bool)
    def on_ippower_bench_on_button_clicked(self, checked):
        self.action_send([
            self.ippower_bench_on_button, self.ippower_bench_off_button
        ], self.backend.ippower_bench_on)

    @Slot(bool)
    def on_ippower_bench_off_button_clicked(self, checked):
        self.action_send([
            self.ippower_bench_off_button, self.ippower_bench_on_button
        ], self.backend.ippower_bench_off)

    @Slot(bool)
    def on_ippower_dm_on_button_clicked(self, checked):
        self.action_send([
            self.ippower_dm_on_button, self.ippower_dm_off_button
        ], self.backend.ippower_dm_on)

    @Slot(bool)
    def on_ippower_dm_off_button_clicked(self, checked):
        self.action_send([
            self.ippower_dm_off_button, self.ippower_dm_on_button
        ], self.backend.ippower_dm_off)

    @Slot(bool)
    def on_dm_on_button_clicked(self, checked):
        self.action_send([self.dm_on_button, self.dm_off_button],
                         self.backend.dm_on)

    @Slot(bool)
    def on_dm_off_button_clicked(self, checked):
        self.action_send([self.dm_off_button, self.dm_on_button],
                         self.backend.dm_off)

    @Slot(bool)
    def on_dm_channels_button_clicked(self, checked):
        if self.dm_channels_window is not None:
            self.dm_channels_window.show()
            self.dm_channels_window.activateWindow()
        else:
            self.dm_channels_window = DMChannelsWindow(
                self.backend, config.AO.DM_loop_number, parent=self)

    @Slot(bool)
    def on_ttm_channels_button_clicked(self, checked):
        if self.ttm_channels_window is not None:
            self.ttm_channels_window.show()
            self.ttm_channels_window.activateWindow()
        else:
            self.ttm_channels_window = DMChannelsWindow(
                self.backend, config.AO.TTM_loop_number, parent=self)

    @Slot(bool)
    def on_dm_calibration_button_clicked(self, checked):
        if self.dm_calibration_window is not None:
            self.dm_calibration_window.show()
            self.dm_calibration_window.activateWindow()
        else:
            self.dm_calibration_window = AOCalibrationWindow(
                self.backend, 'dmloop', config.AO.DM_loop_number, (11, 22),
                (12, 12), parent=self)

    @Slot(bool)
    def on_ttm_calibration_button_clicked(self, checked):
        if self.ttm_calibration_window is not None:
            self.ttm_calibration_window.show()
            self.ttm_calibration_window.activateWindow()
        else:
            self.ttm_calibration_window = AOCalibrationWindow(
                self.backend, 'ttmloop', config.AO.TTM_loop_number, (12, 12),
                (1, 2), parent=self)

    @Slot(bool)
    def on_dm_direct_control_button_clicked(self, checked):
        if self.dm_direct_control_window is not None:
            self.dm_direct_control_window.show()
            self.dm_direct_control_window.activateWindow()
        else:
            self.dm_direct_control_window = DMDirectControlWindow(
                self.backend, parent=self)

    @Slot(bool)
    def on_ttm_direct_control_button_clicked(self, checked):
        if self.ttm_direct_control_window is not None:
            self.ttm_direct_control_window.show()
            self.ttm_direct_control_window.activateWindow()
        else:
            self.ttm_direct_control_window = TTMDirectControlWindow(
                self.backend, parent=self)

    @Slot(bool)
    def on_centering_star_button_clicked(self, checked):
        self.action_send(self.centering_widgets, self.backend.centering_star)

    @Slot(bool)
    def on_centering_laser_button_clicked(self, checked):
        self.action_send(self.centering_widgets, self.backend.centering_laser)

    @Slot(bool)
    def on_centering_spiral_search_button_clicked(self, checked):
        self.action_send(self.centering_widgets, self.backend.centering_spiral)

    @Slot(bool)
    def on_focusing_open_focus_sequence_button_clicked(self, checked):
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.ExistingFiles)
        dialog.setNameFilter('Images (*.fits)')
        dialog.setAcceptMode(QFileDialog.AcceptOpen)

        if config.FITS.focus_data_storage.exists():
            dialog.setDirectory(str(config.FITS.focus_data_storage))

        error_dialog = KMessageBox(self)
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setModal(True)
        error_dialog.setText('<b>Focus sequence loading failed!</b>')

        if dialog.exec():
            filenames = dialog.selectedFiles()

            if len(filenames) == 0:
                error_dialog.setInformativeText(
                    f'Select at least one file (got {len(filenames)}).')
                error_dialog.show()
                return

            error_list = []
            for filename in filenames:
                filename = Path(filename)
                try:
                    if not filename.exists():
                        error_list.append(
                            f'{filename.name}: File does not exists.')
                        continue

                    if filename.suffix.lower() != '.fits':
                        error_list.append(
                            f'{filename.name}: Unsupported file extension "{filename.suffix}".'
                        )
                        continue

                    FocusSequenceWindow(self.backend, filename, parent=self)
                except PermissionError:
                    error_list.append(
                        f'{filename.name}: Can\'t read file, permission refused.'
                    )

            if len(error_list) > 0:
                error_dialog.setInformativeText('\n'.join(error_list))
                error_dialog.show()

    @Slot(bool)
    def on_focusing_autofocus_button_clicked(self, checked):
        self.action_send(self.focusing_autofocus_button,
                         self.backend.focusing_autofocus)

    @Slot(bool)
    def on_focusing_launch_focus_sequence_button_clicked(self, checked):
        self.action_send(self.focusing_launch_focus_sequence_button,
                         self.backend.focusing_sequence)

    @Slot(bool)
    def on_focusing_focus_sequence_button_clicked(self, checked):
        self.open_focus_sequence_window()

    @Slot(bool)
    def on_calibration_poses_button_clicked(self, checked):
        self.open_calibration_poses_window()

    def on_service_action_button_clicked(self, checked, unit, action):
        buttons_list = []

        for key, button in self.services_widgets[unit]['buttons'].items():
            if key != ServiceAction.KILL or action == ServiceAction.KILL:
                buttons_list.append(button)

        self.action_send(buttons_list, self.backend.services_action, unit=unit,
                         action=action)

    @Slot(int)
    def on_deadman_checkbox_stateChanged(self, state):
        if Qt.CheckState(state) == Qt.Checked:
            self.update_deadman()
            self.deadman_timer.start()
        else:
            self.deadman_timer.stop()
            self.reset_deadman()

    def reset_deadman(self):
        self.deadman_count = 0
        self.deadman_label.updateText(count=0, last='--', next='--')

    def update_deadman(self):
        self.deadman_count += 1

        self.action_send([], self.backend.deadman, count=self.deadman_count)

        now = datetime.now()
        next = now + timedelta(
            milliseconds=self.deadman_timer.interval())  #TODO: remainingTime()

        self.deadman_label.updateText(count=self.deadman_count,
                                      last=now.strftime('%H:%M:%S %d-%m-%Y'),
                                      next=next.strftime('%H:%M:%S %d-%m-%Y'))

    @Slot(str)
    def on_iknowwhatido_lineedit_textEdited(self, text):
        enabled = text == 'IKnowWhatIDo'
        self.instrument_shutdown_sequence_button.setEnabledStack(
            enabled, 'password')
        self.rtc_poweroff_button.setEnabledStack(enabled, 'password')
        self.rtc_reboot_button.setEnabledStack(enabled, 'password')

    @Slot(bool)
    def on_instrument_shutdown_sequence_button_clicked(self, checked):
        self.action_send(self.instrument_shutdown_sequence_button,
                         self.backend.instrument_shutdown)

    @Slot(bool)
    def on_rtc_poweroff_button_clicked(self, checked):
        self.action_send(self.rtc_poweroff_button, self.backend.rtc_poweroff)

    @Slot(bool)
    def on_rtc_reboot_button_clicked(self, checked):
        self.action_send(self.rtc_reboot_button, self.backend.rtc_reboot)

    def open_focus_sequence_window(self, force_timer=False):
        if self.focus_sequence_window is not None:
            self.focus_sequence_window.show()
            self.focus_sequence_window.activateWindow()

            if force_timer:
                self.focus_sequence_window.focus_timer.start()
        else:
            self.focus_sequence_window = FocusSequenceWindow(
                self.backend, parent=self)

    def open_calibration_poses_window(self):
        if self.calibration_poses_window is not None:
            self.calibration_poses_window.show()
            self.calibration_poses_window.activateWindow()
        else:
            self.calibration_poses_window = CalibrationPosesWindow(
                self.backend, parent=self)

    def eventFilter(self, source, event):
        if event.type() == QEvent.ToolTip:
            # Disable tooltips
            return True

        if event.type(
        ) == QEvent.ToolTipChange and source == self.activeToolTip:
            self.hovered.emit(source.toolTip())
        if event.type() == QEvent.Enter:
            self.activeToolTip = source
            self.hovered.emit(source.toolTip())
        elif event.type() == QEvent.Leave:
            self.hovered.emit('')

        return QObject.eventFilter(self, source, event)
