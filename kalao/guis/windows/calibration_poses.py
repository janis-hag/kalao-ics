from typing import Any

import numpy as np

from PySide6.QtCore import QEvent, QObject, QTimer
from PySide6.QtGui import QCloseEvent, QShowEvent, Qt
from PySide6.QtWidgets import QAbstractSpinBox, QLineEdit, QSizePolicy, QWidget

from compiled.ui_calibration_poses import Ui_CalibrationPosesWindow

from kalao.utils.json import KalAOJSONDecoder

from kalao.guis.backends.abstract import AbstractBackend
from kalao.guis.utils.definitions import Color
from kalao.guis.utils.mixins import BackendDataMixin
from kalao.guis.utils.string_formatter import KalAOFormatter
from kalao.guis.utils.widgets import (KMainWindow, KNaNDoubleSpinbox,
                                      KStatusIndicator)

from kalao.definitions.dataclasses import CalibrationPose

import config

decoder = KalAOJSONDecoder()


class CalibrationPosesWindow(KMainWindow, BackendDataMixin):
    formatter = KalAOFormatter()

    activeToolTip = None

    def __init__(self, backend: AbstractBackend,
                 parent: QWidget = None) -> None:
        super().__init__(parent)

        self.backend = backend

        self.ui = Ui_CalibrationPosesWindow()
        self.ui.setupUi(self)

        self.resize(600, 900)

        self.ui.flats_label.updateText(
            target=config.Calib.Flats.target_adu,
            min_exposure_time=config.Calib.Flats.min_exptime,
            max_exposure_time=config.Calib.Flats.max_exptime)

        self.ui.done_label.updateText(current_calib=np.nan, total_calib=np.nan)

        self.calibration_widgets = []

        backend.all_updated.connect(self.all_updated)

        backend.calibration_sequence_updated.connect(
            self.calibration_sequence_updated)

        self.calib_timer = QTimer(parent=self)
        self.calib_timer.setInterval(
            int(1000 / config.GUI.refreshrate_auxillary))
        self.calib_timer.timeout.connect(backend.calibration_sequence)
        self.calib_timer.start()

        self.show()
        self.center()

    def all_updated(self, data: dict[str, Any]) -> None:
        camera_status = self.consume_dict(data, 'camera', 'camera_status')
        if camera_status is not None:
            self.ui.camera_status_lineedit.setText(camera_status)

        exposure_time = self.consume_dict(data, 'camera', 'exposure_time')
        if exposure_time is not None:
            self.ui.camera_exposure_time_spinbox.setValue(exposure_time)

        remaining_time = self.consume_dict(data, 'camera', 'remaining_time')
        if remaining_time is not None:
            self.ui.camera_remaining_time_spinbox.setValue(remaining_time)

        filter_name = self.consume_dict(data, 'hw', 'filterwheel_filter_name')
        if filter_name is not None:
            self.ui.filterwheel_filter_lineedit.setText(filter_name)

        tungsten_status = self.consume_dict(data, 'hw', 'tungsten_status')
        if tungsten_status is not None:
            self.ui.tungsten_status_lineedit.setText(tungsten_status)

        shutter_status = self.consume_dict(data, 'hw', 'shutter_status')
        if shutter_status is not None:
            self.ui.shutter_status_lineedit.setText(shutter_status)

    def calibration_sequence_updated(self, data: dict[str, Any]) -> None:
        calibration_poses = self.consume_dict(data, 'memory',
                                              'calibration_poses')

        if calibration_poses is not None:
            self.update_calibs(decoder.decode(calibration_poses['list']))

    def update_widgets(self, length: int) -> None:
        while len(self.calibration_widgets) < length:
            type_lineedit = QLineEdit(self)
            type_lineedit.setReadOnly(True)
            type_lineedit.setAlignment(Qt.AlignmentFlag.AlignHCenter)

            filter_lineedit = QLineEdit(self)
            filter_lineedit.setReadOnly(True)
            filter_lineedit.setAlignment(Qt.AlignmentFlag.AlignHCenter)

            exposure_time_spinbox = KNaNDoubleSpinbox(self)
            exposure_time_spinbox.setReadOnly(True)
            exposure_time_spinbox.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            exposure_time_spinbox.setDecimals(3)
            exposure_time_spinbox.setMinimum(0)
            exposure_time_spinbox.setMaximum(999999)
            exposure_time_spinbox.setSuffix(' s')
            exposure_time_spinbox.setButtonSymbols(
                QAbstractSpinBox.ButtonSymbols.NoButtons)

            median_spinbox = KNaNDoubleSpinbox(self)
            median_spinbox.setReadOnly(True)
            median_spinbox.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            median_spinbox.setDecimals(1)
            median_spinbox.setMinimum(0)
            median_spinbox.setMaximum(65535)
            median_spinbox.setSuffix(' ADU')
            median_spinbox.setButtonSymbols(
                QAbstractSpinBox.ButtonSymbols.NoButtons)

            status_indicator = KStatusIndicator()
            status_indicator.setCursor(Qt.CursorShape.WhatsThisCursor)
            status_indicator.installEventFilter(self)
            status_indicator.setFixedSize(20, 20)
            status_indicator.setSizePolicy(QSizePolicy.Policy.Fixed,
                                           QSizePolicy.Policy.Fixed)

            row = len(self.calibration_widgets) + 1

            self.calibration_widgets.append({
                'type': type_lineedit,
                'filter': filter_lineedit,
                'exposure_time': exposure_time_spinbox,
                'median': median_spinbox,
                'status': status_indicator,
            })

            self.ui.calibration_layout.addWidget(type_lineedit, row, 0)
            self.ui.calibration_layout.addWidget(filter_lineedit, row, 1)
            self.ui.calibration_layout.addWidget(exposure_time_spinbox, row, 2)
            self.ui.calibration_layout.addWidget(median_spinbox, row, 3)
            self.ui.calibration_layout.addWidget(status_indicator, row, 4,
                                                 Qt.AlignmentFlag.AlignHCenter)

        while len(self.calibration_widgets) > length:
            for widget in self.calibration_widgets[-1].values():
                self.ui.calibration_layout.removeWidget(widget)
                widget.deleteLater()

            self.calibration_widgets.pop()

    def update_calibs(self, calib_list: list[CalibrationPose]) -> None:
        self.update_widgets(len(calib_list))

        current_calib = -1

        for i in range(len(calib_list)):
            calib = calib_list[i]
            w = self.calibration_widgets[i]

            w['type'].setText(calib.template.id.name)

            if calib.filter is None:
                w['filter'].setText('N/A')
            else:
                w['filter'].setText(calib.filter)

            w['exposure_time'].setValue(calib.exposure_time)

            w['median'].setValue(calib.median)

            if calib.status == 'IDLE':
                w['status'].setStatus(Color.BLACK, calib.status)
            elif calib.status == 'OK':
                w['status'].setStatus(Color.GREEN, calib.status)
                current_calib = i
            elif calib.status == 'EXPOSING':
                w['status'].setStatus(Color.BLUE, calib.status)
                current_calib = i
            elif calib.status == 'SKIPPED':
                status = calib.status
                if calib.error_text != '':
                    status += f' ({calib.error_text})'
                w['status'].setStatus(Color.ORANGE, status)
                current_calib = i
            else:  # ERROR
                status = calib.status
                if calib.error_text != '':
                    status += f' ({calib.error_text})'
                w['status'].setStatus(Color.RED, status)
                current_calib = i

        if current_calib > 0:
            self.ui.scrollArea.ensureWidgetVisible(
                self.calibration_widgets[current_calib]['status'])

        self.ui.done_label.updateText(current_calib=current_calib + 1,
                                      total_calib=len(calib_list))

    def closeEvent(self, event: QCloseEvent) -> None:
        self.calib_timer.stop()

        return super().closeEvent(event)

    def showEvent(self, event: QShowEvent) -> None:
        QTimer.singleShot(0, self.backend, self.backend.calibration_sequence)

        self.calib_timer.start()

        return super().showEvent(event)

    def eventFilter(self, source: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.ToolTip:
            # Disable tooltips
            return True

        if event.type(
        ) == QEvent.Type.ToolTipChange and source == self.activeToolTip:
            self.info_to_statusbar(source.toolTip())
        if event.type() == QEvent.Type.Enter:
            self.activeToolTip = source
            self.info_to_statusbar(source.toolTip())
        elif event.type() == QEvent.Type.Leave:
            self.activeToolTip = None
            self.info_to_statusbar('')

        return QObject.eventFilter(self, source, event)
