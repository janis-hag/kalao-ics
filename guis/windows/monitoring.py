import numpy as np

from PySide6.QtWidgets import (QGridLayout, QGroupBox, QHBoxLayout, QLabel,
                               QLineEdit, QSizePolicy, QSpacerItem,
                               QVBoxLayout)

from kalao.utils import database

from guis.kalao.mixins import BackendDataMixin
from guis.kalao.widgets import KalAOWidget


class MonitoringWidget(KalAOWidget, BackendDataMixin):
    def __init__(self, backend, parent=None):
        super().__init__(parent)

        self.backend = backend

        self.resize(600, 400)

        self.setLayout(QHBoxLayout())

        self.layout().addLayout(QVBoxLayout())
        self.layout().addLayout(QVBoxLayout())
        self.layout().addLayout(QVBoxLayout())
        self.layout().addLayout(QVBoxLayout())
        self.layout().addLayout(QVBoxLayout())

        self.groupboxes = {}
        self.lineedits = {}

        for key, info in database.definitions['monitoring']['metadata'].items(
        ):
            self.add_item('monitoring', key, info)

        for key, info in database.definitions['telemetry']['metadata'].items():
            self.add_item('telemetry', key, info)

        column_length = np.zeros(self.layout().count())
        for groupbox in sorted(self.groupboxes.values(),
                               key=lambda g: g.layout().count(), reverse=True):
            i = np.argmin(column_length)

            groupbox.layout().addItem(
                QSpacerItem(20, 40, QSizePolicy.Minimum,
                            QSizePolicy.Expanding))

            self.layout().itemAt(i).addWidget(groupbox)
            column_length[i] += groupbox.layout().count()

        for lineedit in self.lineedits.values():
            lineedit.setText(f'--{lineedit.unit}')

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

        lineedit.collection = collection
        lineedit.key = key

        row = groupbox.layout().rowCount()
        groupbox.layout().addWidget(label, row, 0)
        groupbox.layout().addWidget(lineedit, row, 1)

        self.lineedits[f'{collection}/{key}'] = lineedit

    def monitoringandtelemetry_updated(self, data):
        for lineedit in self.lineedits.values():
            value_timestamp = self.consume_db(data, lineedit.collection,
                                              lineedit.key)
            if value_timestamp is not None:
                value, timestamp = value_timestamp
                lineedit.setText(f'{value}{lineedit.unit}')
                lineedit.setToolTip(timestamp.strftime('%Y-%m-%d %H:%M:%S'))
