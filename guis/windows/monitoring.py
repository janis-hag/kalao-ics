from datetime import datetime, timezone

import numpy as np

from PySide6.QtWidgets import (QGridLayout, QGroupBox, QLabel, QLineEdit,
                               QSizePolicy, QSpacerItem, QVBoxLayout)

from kalao.utils import database

from guis.kalao.definitions import Color
from guis.kalao.mixins import BackendDataMixin
from guis.kalao.string_formatter import KalAOFormatter
from guis.kalao.ui_loader import loadUi
from guis.kalao.widgets import KalAOWidget

import config


class MonitoringWidget(KalAOWidget, BackendDataMixin):
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

        for key, info in database.definitions['monitoring']['metadata'].items(
        ):
            self.add_item('monitoring', key, info)

        for key, info in database.definitions['telemetry']['metadata'].items():
            self.add_item('telemetry', key, info)

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

    def add_item(self, collection, key, info):
        group = info.get('group', 'Generic')

        groupbox = self.groupboxes.get(group)
        if groupbox is None:
            groupbox = QGroupBox(group)
            groupbox.setLayout(QGridLayout())

            self.groupboxes[group] = groupbox

        label = QLabel(info.get('short'))
        label.setToolTipDuration(2147483647)
        label.setToolTip(info.get('long'))

        lineedit = QLineEdit()
        lineedit.setToolTipDuration(2147483647)
        lineedit.setReadOnly(True)

        unit = info.get('unit')
        if unit is None or unit == '':
            lineedit.unit = ''
        else:
            lineedit.unit = ' ' + unit

        lineedit.setText(f'--{lineedit.unit}')

        lineedit.collection = collection
        lineedit.key = key
        lineedit.timestamp = datetime.fromtimestamp(0, tz=timezone.utc)

        row = groupbox.layout().rowCount()
        groupbox.layout().addWidget(label, row, 0)
        groupbox.layout().addWidget(lineedit, row, 1)

        self.lineedits[f'{collection}/{key}'] = lineedit

    def monitoringandtelemetry_updated(self, data):
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
                lineedit.setToolTip(
                    timestamp.astimezone().strftime('%H:%M:%S %d-%m-%Y'))
                lineedit.timestamp = timestamp

            max_age = 2 * config.Database.monitoring_update_interval

            if (datetime.now(timezone.utc) -
                    lineedit.timestamp).total_seconds() > max_age:
                lineedit.setStyleSheet(f'color: {Color.GREY.name()};')
            else:
                lineedit.setStyleSheet(f'')

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
