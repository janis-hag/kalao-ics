from datetime import datetime, timezone

import numpy as np

from PySide6.QtCore import QEvent, QObject, Signal
from PySide6.QtGui import Qt
from PySide6.QtWidgets import (QGridLayout, QGroupBox, QLabel, QLineEdit,
                               QSizePolicy, QSpacerItem, QVBoxLayout)

from kalao import database
from kalao.timers import monitoring
from kalao.utils import kstring

from kalao.guis.utils.definitions import Color
from kalao.guis.utils.mixins import BackendDataMixin
from kalao.guis.utils.string_formatter import KalAOFormatter
from kalao.guis.utils.ui_loader import loadUi
from kalao.guis.utils.widgets import KWidget

from kalao.definitions.enums import AlarmLevel

import config


class MonitoringWidget(KWidget, BackendDataMixin):
    hovered = Signal(str)
    updated = Signal(int, int, int)

    activeToolTip = None

    formatter = KalAOFormatter()

    def __init__(self, backend, parent=None):
        super().__init__(parent)

        self.backend = backend

        loadUi('monitoring.ui', self)
        self.resize(600, 400)

        self.data_layout.addLayout(QVBoxLayout())
        self.data_layout.addLayout(QVBoxLayout())
        self.data_layout.addLayout(QVBoxLayout())
        self.data_layout.addLayout(QVBoxLayout())
        self.data_layout.addLayout(QVBoxLayout())

        self.groupboxes = {}
        self.lineedits = {}

        for key, metadata in database.definitions['monitoring'][
                'metadata'].items():
            self.add_item('monitoring', key, metadata)

        column_length = np.zeros(self.data_layout.count())
        for groupbox in sorted(self.groupboxes.values(),
                               key=lambda g: g.layout().count(), reverse=True):
            i = np.argmin(column_length)

            groupbox.layout().addItem(
                QSpacerItem(20, 40, QSizePolicy.Minimum,
                            QSizePolicy.Expanding))

            self.data_layout.itemAt(i).addWidget(groupbox)
            column_length[i] += groupbox.layout().count(
            ) + 1  # +1 to account space taken by title

        self.backend.monitoring_updated.connect(self.monitoring_updated)

    def add_item(self, collection, key, metadata):
        group = metadata.get('group', 'Generic')

        groupbox = self.groupboxes.get(group)
        if groupbox is None:
            groupbox = QGroupBox(group)
            groupbox.setLayout(QGridLayout())

            self.groupboxes[group] = groupbox

        label = QLabel(metadata.get('short'))
        label.setCursor(Qt.WhatsThisCursor)
        label.setToolTip(metadata.get('long'))
        label.installEventFilter(self)

        lineedit = QLineEdit()
        lineedit.setReadOnly(True)
        lineedit.setCursor(Qt.WhatsThisCursor)
        lineedit.collection = collection
        lineedit.key = key
        lineedit.timestamp = None
        lineedit.value = None
        lineedit.metadata = metadata
        lineedit.unit = kstring.get_unit_string(metadata)
        lineedit.ranges = ''
        lineedit.rounding = lineedit.metadata.get('rounding')
        lineedit.installEventFilter(self)

        alarm_range = lineedit.metadata.get('alarm_range', [np.nan, np.nan])
        warn_range = lineedit.metadata.get('warn_range', [np.nan, np.nan])

        alarm_values = lineedit.metadata.get('alarm_values', [])
        alarm_min = alarm_range[0]
        alarm_max = alarm_range[1]
        warn_min = warn_range[0]
        warn_max = warn_range[1]

        if not np.isnan(warn_min) or not np.isnan(warn_max):
            lineedit.ranges += self.formatter.format(
                ' | Warning range: [{warn_min}{unit}; {warn_max}{unit}]',
                warn_min=warn_min, warn_max=warn_max, unit=lineedit.unit)

        if not np.isnan(alarm_min) or not np.isnan(alarm_min):
            lineedit.ranges += self.formatter.format(
                ' | Alarm range: [{alarm_min}{unit}; {alarm_max}{unit}]',
                alarm_min=alarm_min, alarm_max=alarm_max, unit=lineedit.unit)

        if len(alarm_values) > 0:
            lineedit.ranges += ' | Alarm values: ' + ', '.join(
                self.formatter.format('{value}{unit}', value=value,
                                      unit=lineedit.unit)
                for value in alarm_values)

        lineedit.setText('No data')
        lineedit.setToolTip(f'No data{lineedit.ranges}')
        lineedit.setStyleSheet(f'background-color: {Color.GREY.name()};')

        row = groupbox.layout().rowCount()
        groupbox.layout().addWidget(label, row, 0)
        groupbox.layout().addWidget(lineedit, row, 1)

        self.lineedits[f'{collection}/{key}'] = lineedit

    def monitoring_updated(self, data):
        outdated = 0
        alarms = 0
        warnings = 0

        for lineedit in self.lineedits.values():
            value, timestamp = self.consume_db(data, lineedit.collection,
                                               lineedit.key)
            if value is not None:
                if lineedit.rounding is None:
                    text = f'{value}{lineedit.unit}'
                else:
                    text = self.formatter.format(
                        f'{{value:.{lineedit.rounding}f}}{{lineedit.unit}}',
                        value=value, lineedit=lineedit)

                lineedit.setText(text)
                lineedit.timestamp = timestamp
                lineedit.value = value

            if lineedit.timestamp is None:
                continue

            timestamp_text = f'Timestamp: {lineedit.timestamp.astimezone():%H:%M:%S %d-%m-%Y}'

            if (datetime.now(timezone.utc) - lineedit.timestamp
                ).total_seconds() > config.GUI.monitoring_max_age:
                lineedit.setStyleSheet(
                    f'background-color: {Color.GREY.name()};')
                lineedit.setToolTip(
                    f'{timestamp_text} (outdated){lineedit.ranges}')
                outdated += 1
            else:
                alarm = monitoring.check_alarms(lineedit.key, lineedit.value)

                if alarm.level == AlarmLevel.ALARM:
                    lineedit.setStyleSheet(
                        f'background-color: {Color.RED.name()};')
                    alarms += 1
                elif alarm.level == AlarmLevel.WARNING:
                    lineedit.setStyleSheet(
                        f'background-color: {Color.ORANGE.name()};')
                    warnings += 1
                else:
                    lineedit.setStyleSheet(
                        f'background-color: {Color.GREEN.name()};')

                lineedit.setToolTip(f'{timestamp_text}{lineedit.ranges}')

        monitoring_timestamp = self.consume_dict(data, 'db-timestamps',
                                                 'monitoring')
        if monitoring_timestamp is not None:
            self.last_update_label.updateText(
                last_update=monitoring_timestamp.astimezone().strftime(
                    '%H:%M:%S %d-%m-%Y'))

            if (datetime.now(timezone.utc) - monitoring_timestamp
                ).total_seconds() > config.GUI.monitoring_max_age:
                self.last_update_label.setStyleSheet(
                    f'color: {Color.RED.name()};')
                alarms += 1
            else:
                self.last_update_label.setStyleSheet(
                    f'color: {Color.BLACK.name()};')

        self.updated.emit(outdated, warnings, alarms)

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
