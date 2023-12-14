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

from kalao.definitions.enums import (FlipMirrorPosition, IPPowerStatus,
                                     ServiceAction, ShutterState)

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
            for state in ShutterState:
                if state != ShutterState.ERROR:
                    self.shutter_combobox.addItem(state, state)

        with QSignalBlocker(self.flipmirror_combobox):
            for position in FlipMirrorPosition:
                if position != FlipMirrorPosition.ERROR:
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
        self.data_to_widget(self.consume_dict(data, 'plc', 'shutter_state'),
                            self.shutter_combobox)
        self.data_to_widget(
            self.consume_dict(data, 'plc', 'flip_mirror_position'),
            self.flipmirror_combobox)
        self.data_to_widget(
            self.consume_dict(data, 'plc', 'calib_unit_position'),
            self.calibunit_spinbox)
        self.data_to_widget(self.consume_dict(data, 'plc', 'tungsten_state'),
                            self.tungsten_enabled_checkbox, true_value='ON')
        self.data_to_widget(self.consume_dict(data, 'plc', 'laser_state'),
                            self.tungsten_enabled_checkbox, true_value='ON')
        self.data_to_widget(self.consume_dict(data, 'plc', 'laser_power'),
                            self.laser_intensity_spinbox)
        self.data_to_widget(
            self.consume_dict(data, 'plc', 'filterwheel_filter_name'),
            self.filterwheel_combobox)
        self.data_to_widget(self.consume_dict(data, 'plc', 'adc1_angle'),
                            self.adc1_spinbox)
        self.data_to_widget(self.consume_dict(data, 'plc', 'adc2_angle'),
                            self.adc2_spinbox)

        ippower_rtc_status = self.consume_dict(data, 'ippower',
                                               'ippower_rtc_status')
        if ippower_rtc_status is not None:
            if ippower_rtc_status == IPPowerStatus.ON:
                self.ippower_rtc_indicator.setStatus(Color.GREEN,
                                                     ippower_rtc_status.name)
            else:
                self.ippower_rtc_indicator.setStatus(Color.RED,
                                                     ippower_rtc_status.name)
                #TODO: if error?

        ippower_bench_status = self.consume_dict(data, 'ippower',
                                                 'ippower_bench_status')
        if ippower_bench_status is not None:
            if ippower_bench_status == IPPowerStatus.ON:
                self.ippower_bench_indicator.setStatus(
                    Color.GREEN, ippower_bench_status.name)
            else:
                self.ippower_bench_indicator.setStatus(
                    Color.RED, ippower_bench_status.name)
                # TODO: if error?

        ippower_dm_status = self.consume_dict(data, 'ippower',
                                              'ippower_dm_status')
        if ippower_dm_status is not None:
            if ippower_dm_status == IPPowerStatus.ON:
                self.ippower_dm_indicator.setStatus(Color.GREEN,
                                                    ippower_dm_status.name)
            else:
                self.ippower_dm_indicator.setStatus(Color.RED,
                                                    ippower_dm_status.name)
                # TODO: if error?

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
                if status[0] == 'active':
                    widgets['indicator'].setStatus(Color.GREEN, status[0])
                else:
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
    def on_tungsten_enabled_checkbox_stateChanged(self, state):
        self.action_send(self.tungsten_enabled_checkbox,
                         self.backend.set_plc_tungsten_state,
                         Qt.CheckState(state) == Qt.Checked)

    @Slot(int)
    def on_laser_enabled_checkbox_stateChanged(self, state):
        self.action_send(self.laser_enabled_checkbox,
                         self.backend.set_plc_laser_state,
                         Qt.CheckState(state) == Qt.Checked)

    @Slot(float)
    def on_laser_intensity_spinbox_valueChanged(self, d):
        self.action_send(self.laser_intensity_spinbox,
                         self.backend.set_plc_laser_intensity, d)

    @Slot(int)
    def on_filterwheel_combobox_currentIndexChanged(self, index):
        self.action_send(self.filterwheel_combobox,
                         self.backend.set_plc_filterwheel_filter,
                         self.filterwheel_combobox.currentData())

    @Slot(float)
    def on_adc1_spinbox_valueChanged(self, d):
        self.action_send(self.adc1_spinbox,
                         self.backend.set_plc_adc_1_position, d)

    @Slot(float)
    def on_adc2_spinbox_valueChanged(self, d):
        self.action_send(self.adc2_spinbox,
                         self.backend.set_plc_adc_2_position, d)

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
