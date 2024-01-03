from datetime import datetime, timezone

import numpy as np

from PySide6.QtCore import QEvent, QObject, Signal
from PySide6.QtGui import Qt
from PySide6.QtWidgets import (QGridLayout, QGroupBox, QLabel, QLineEdit,
                               QSizePolicy, QSpacerItem, QVBoxLayout)

from kalao import database
from kalao.utils import kalao_string

from guis.kalao.definitions import Color
from guis.kalao.mixins import BackendDataMixin
from guis.kalao.string_formatter import KalAOFormatter
from guis.kalao.ui_loader import loadUi
from guis.kalao.widgets import KWidget

import config


class MonitoringWidget(KWidget, BackendDataMixin):
    hovered = Signal(str)
    updated = Signal(int, int, int)

    formatter = KalAOFormatter()

    def __init__(self, backend, parent=None):
        super().__init__(parent)

        self.backend = backend

        loadUi('monitoring.ui', self)
        self.resize(600, 400)

        self.monitoring_interval_label.updateText(
            monitoring_interval=config.Database.monitoring_update_interval)
        self.telemetry_interval_label.updateText(
            telemetry_interval=config.Database.telemetry_update_interval)

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

        for key, metadata in database.definitions['telemetry'][
                'metadata'].items():
            self.add_item('telemetry', key, metadata)

        column_length = np.zeros(self.data_layout.count())
        for groupbox in sorted(self.groupboxes.values(),
                               key=lambda g: g.layout().count(), reverse=True):
            i = np.argmin(column_length)

            groupbox.layout().addItem(
                QSpacerItem(20, 40, QSizePolicy.Minimum,
                            QSizePolicy.Expanding))

            self.data_layout.itemAt(i).addWidget(groupbox)
            column_length[i] += groupbox.layout().count()

        self.backend.monitoringandtelemetry_updated.connect(
            self.monitoringandtelemetry_updated)

    def add_item(self, collection, key, metadata):
        group = metadata.get('group', 'Generic')

        groupbox = self.groupboxes.get(group)
        if groupbox is None:
            groupbox = QGroupBox(group)
            groupbox.setLayout(QGridLayout())

            self.groupboxes[group] = groupbox

        label = QLabel(metadata.get('short'))
        label.setCursor(Qt.WhatsThisCursor)
        label.hover_text = metadata.get('long')
        label.installEventFilter(self)

        lineedit = QLineEdit()
        lineedit.setReadOnly(True)
        lineedit.setCursor(Qt.WhatsThisCursor)
        lineedit.collection = collection
        lineedit.key = key
        lineedit.timestamp = None
        lineedit.metadata = metadata
        lineedit.unit = kalao_string.get_unit_string(metadata)
        lineedit.hover_text = 'No data'
        lineedit.installEventFilter(self)

        lineedit.setText(f'--{lineedit.unit}')
        lineedit.setStyleSheet(f'color: {Color.GREY.name()};')

        row = groupbox.layout().rowCount()
        groupbox.layout().addWidget(label, row, 0)
        groupbox.layout().addWidget(lineedit, row, 1)

        self.lineedits[f'{collection}/{key}'] = lineedit

    def monitoringandtelemetry_updated(self, data):
        outdated = 0
        errors = 0
        warnings = 0

        for lineedit in self.lineedits.values():
            value, timestamp = self.consume_db(data, lineedit.collection,
                                               lineedit.key)
            if value is not None:
                if isinstance(value, float):
                    text = self.formatter.format('{value:.3g}{lineedit.unit}',
                                                 value=value,
                                                 lineedit=lineedit)
                else:
                    text = f'{value}{lineedit.unit}'

                lineedit.setText(text)
                lineedit.timestamp = timestamp

            if lineedit.timestamp is None:
                continue

            max_age = 2 * config.Database.monitoring_update_interval

            since_text = f'Since: {lineedit.timestamp.astimezone().strftime("%H:%M:%S %d-%m-%Y")}'

            if (datetime.now(timezone.utc) -
                    lineedit.timestamp).total_seconds() > max_age:
                lineedit.setStyleSheet(f'color: {Color.GREY.name()};')
                lineedit.hover_text = f'{since_text} (outdated)'
                outdated += 1
            elif isinstance(value, float) or isinstance(value, int):
                error_range = lineedit.metadata.get('error_range',
                                                    [np.nan, np.nan])
                warn_range = lineedit.metadata.get('warn_range',
                                                   [np.nan, np.nan])

                error_min = error_range[0]
                error_max = error_range[1]
                warn_min = warn_range[0]
                warn_max = warn_range[1]

                if value > error_max or value < error_min:
                    lineedit.setStyleSheet(f'color: {Color.RED.name()};')
                    lineedit.hover_text = self.formatter.format(
                        '{since_text} | Outside of error range [{error_min}{unit}; {error_max}{unit}]',
                        since_text=since_text, error_min=error_min,
                        error_max=error_max, unit=lineedit.unit)
                    errors += 1
                elif value > warn_max or value < warn_min:
                    lineedit.setStyleSheet(f'color: {Color.ORANGE.name()};')
                    lineedit.hover_text = self.formatter.format(
                        '{since_text} | Outside of warning range [{warn_min}{unit}; {warn_max}{unit}]',
                        since_text=since_text, warn_min=warn_min,
                        warn_max=warn_max, unit=lineedit.unit)
                    warnings += 1
                else:
                    lineedit.setStyleSheet(f'color: {Color.BLACK.name()};')
                    lineedit.hover_text = since_text
            else:
                lineedit.setStyleSheet(f'color: {Color.BLACK.name()};')
                lineedit.hover_text = since_text

        monitoring = self.consume_dict(data, 'db-timestamps', 'monitoring')
        if monitoring is not None:
            self.monitoring_update_label.updateText(
                monitoring_update=monitoring.astimezone().strftime(
                    '%H:%M:%S %d-%m-%Y'))

        telemetry = self.consume_dict(data, 'db-timestamps', 'telemetry')
        if telemetry is not None:
            self.telemetry_update_label.updateText(
                telemetry_update=telemetry.astimezone().strftime(
                    '%H:%M:%S %d-%m-%Y'))

        self.updated.emit(outdated, warnings, errors)

    def eventFilter(self, source, event):
        if hasattr(source, 'hover_text'):
            if event.type() == QEvent.Enter:
                self.hovered.emit(source.hover_text)
            elif event.type() == QEvent.Leave:
                self.hovered.emit('')
        return QObject.eventFilter(self, source, event)
