from datetime import timezone

import numpy as np

from PySide6.QtCharts import QDateTimeAxis, QLineSeries, QValueAxis, QXYSeries
from PySide6.QtCore import (QDateTime, QEvent, QObject, QPointF,
                            QSignalBlocker, QTimer, QTimeZone, Signal, Slot)
from PySide6.QtGui import QCursor, QGuiApplication, QPen, Qt
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QPushButton

from kalao import database
from kalao.utils import kalao_string, kalao_time

from guis.kalao.definitions import ColorPalette
from guis.kalao.ui_loader import loadUi
from guis.kalao.widgets import KalAOListWidgetItem, KalAOWidget

import config


class PlotsWidget(KalAOWidget):
    hovered = Signal(str)
    point_size = 3

    current_index = -1

    live_timer = QTimer()

    def __init__(self, backend, parent=None):
        super().__init__(parent)

        self.backend = backend

        loadUi('plots.ui', self)
        self.resize(600, 400)

        self.groups = {}
        self.items = {}

        for k, v in sorted(
                database.definitions['telemetry']['metadata'].items(),
                key=lambda t: t[1]['short'].casefold()):
            item = KalAOListWidgetItem(k, self.get_display_name(v))
            item.hover_text = v['long']
            # item.installEventFilter(self)

            group = v.get('group', 'Generic')
            if group not in self.groups:
                self.groups[group] = []
            self.groups[group].append(('telemetry', k))

            self.telemetry_list.addItem(item)
            self.items[f'telemetry/{k}'] = item
        self.telemetry_list.installEventFilter(self)

        for k, v in sorted(
                database.definitions['monitoring']['metadata'].items(),
                key=lambda t: t[1]['short'].casefold()):
            item = KalAOListWidgetItem(k, self.get_display_name(v))
            item.hover_text = v['long']
            # item.installEventFilter(self)

            group = v.get('group', 'Generic')
            if group not in self.groups:
                self.groups[group] = []
            self.groups[group].append(('monitoring', k))

            self.monitoring_list.addItem(item)
            self.items[f'monitoring/{k}'] = item
        self.monitoring_list.installEventFilter(self)

        for k, v in sorted(database.definitions['obs']['metadata'].items(),
                           key=lambda t: t[1]['short'].casefold()):
            if k in config.GUI.plots_exclude_list:
                continue

            item = KalAOListWidgetItem(k, self.get_display_name(v))
            item.hover_text = v['long']
            # item.installEventFilter(self)
            self.obs_list.addItem(item)

            self.items[f'obs/{k}'] = item
        self.obs_list.installEventFilter(self)

        # Create Chart and set General Chart setting
        chart = self.plots_view.chart

        # X Axis Settings
        self.axis_x = QDateTimeAxis()
        self.axis_x.setTickCount(13)
        self.axis_x.setFormat("HH:mm")
        self.axis_x.setRange(self.start_datetimeedit.dateTime(),
                             self.end_datetimeedit.dateTime())
        chart.addAxis(self.axis_x, Qt.AlignBottom)

        # Y Axis Settings
        self.axis_y = QValueAxis()
        self.axis_y.setTickCount(20)
        self.axis_y.setRange(-1, 1)
        chart.addAxis(self.axis_y, Qt.AlignLeft)

        #chart.legend().hide()

        ### Group buttons

        for group in sorted(self.groups.keys(),
                            key=lambda key: key.casefold()):
            button = QPushButton(group)
            button.clicked.connect(lambda checked=False, group=group: self.
                                   on_group_button_clicked(checked, group))
            self.group_layout.addWidget(button)

        self.plots_view.chart.hovered.connect(self.hover_xy_to_str)

        self.on_tonight_button_clicked(None)

    def get_display_name(self, metadata):
        unit = metadata.get('unit')
        if unit is None or unit == '':
            unit = ' [-]'
        else:
            unit = f' [{unit}]'

        return f'{metadata["short"]}{unit}'

    def on_group_button_clicked(self, checked, group):
        self.on_reset_button_clicked(checked)

        for collection, key in self.groups[group]:
            item = self.items[f'{collection}/{key}']
            item.setSelected(True)

            if collection == 'monitoring':
                self.monitoring_list.scrollToItem(item)
            elif collection == 'telemetry':
                self.telemetry_list.scrollToItem(item)
            elif collection == 'obs':
                self.obs_list.scrollToItem(item)

    @Slot(QListWidgetItem)
    def on_telemetry_list_itemEntered(self, item):
        self.hovered.emit(item.hover_text)

    @Slot(QListWidgetItem)
    def on_monitoring_list_itemEntered(self, item):
        self.hovered.emit(item.hover_text)

    @Slot(QListWidgetItem)
    def on_obs_list_itemEntered(self, item):
        self.hovered.emit(item.hover_text)

    @Slot(bool)
    def on_reset_button_clicked(self, checked):
        self.monitoring_list.clearSelection()
        self.telemetry_list.clearSelection()
        self.obs_list.clearSelection()

        self.monitoring_list.scrollToTop()
        self.telemetry_list.scrollToTop()
        self.obs_list.scrollToTop()

    @Slot(QDateTime)
    def on_start_datetimeedit_dateTimeChanged(self, datetime):
        self.end_datetimeedit.setMinimumDateTime(datetime)

        self.axis_x.setRange(self.start_datetimeedit.dateTime(),
                             self.end_datetimeedit.dateTime())

    @Slot(QDateTime)
    def on_end_datetimeedit_dateTimeChanged(self, datetime):
        self.start_datetimeedit.setMaximumDateTime(datetime)

        self.axis_x.setRange(self.start_datetimeedit.dateTime(),
                             self.end_datetimeedit.dateTime())

    @Slot(float)
    def on_min_spinbox_valueChanged(self, d):
        self.max_spinbox.setMinimum(d)
        self.axis_y.setMin(d)

    @Slot(float)
    def on_max_spinbox_valueChanged(self, d):
        self.min_spinbox.setMaximum(d)
        self.axis_y.setMax(d)

    @Slot(bool)
    def on_last_hour_button_clicked(self, checked):
        now = QDateTime.currentDateTime()
        prev = now.addSecs(-3600)

        self.start_datetimeedit.setDateTime(prev)
        self.end_datetimeedit.setDateTime(now)

    @Slot(bool)
    def on_tonight_button_clicked(self, checked):
        start_of_night = kalao_time.get_start_of_night(kalao_time.now())

        start = QDateTime.fromSecsSinceEpoch(int(start_of_night.timestamp()))
        end = start.addSecs(86400)

        self.start_datetimeedit.setDateTime(start)
        self.end_datetimeedit.setDateTime(end)

    @Slot(int)
    def on_live_checkbox_stateChanged(self, state):
        if Qt.CheckState(state) == Qt.Checked:
            self.live_timer.setInterval(int(1000 / config.GUI.refreshrate_dbs))
            self.live_timer.timeout.connect(self.on_live_timer_timeout)

            self.on_live_timer_timeout()
            self.live_timer.start()
        else:
            self.live_timer.stop()

    def on_live_timer_timeout(self):
        time_delta = self.end_datetimeedit.dateTime().msecsTo(
            self.start_datetimeedit.dateTime())

        now = QDateTime.currentDateTime()
        prev = now.addMSecs(time_delta)

        self.end_datetimeedit.setDateTime(now)
        self.start_datetimeedit.setDateTime(prev)

        self.on_plot_button_clicked()

    @Slot(bool)
    def on_plot_button_clicked(self, checked=None):
        monitoring_keys = []
        telemetry_keys = []
        obs_keys = []

        for item in self.monitoring_list.selectedItems():
            monitoring_keys.append(item.key)

        for item in self.telemetry_list.selectedItems():
            telemetry_keys.append(item.key)

        for item in self.obs_list.selectedItems():
            obs_keys.append(item.key)

        dt_start = self.start_datetimeedit.dateTime().toUTC().toPython(
        ).replace(tzinfo=timezone.utc)
        dt_end = self.end_datetimeedit.dateTime().toUTC().toPython().replace(
            tzinfo=timezone.utc)

        QGuiApplication.setOverrideCursor(QCursor(Qt.BusyCursor))

        data = self.backend.plots_data(dt_start, dt_end, monitoring_keys,
                                       telemetry_keys, obs_keys)

        QGuiApplication.restoreOverrideCursor()

        chart = self.plots_view.chart

        chart.removeAllSeries()
        self.series = {}
        self.value_before_conversion = {}

        color_index = 0
        plot_min = np.inf
        plot_max = -np.inf

        for name, collection in data.items():
            if collection.empty:
                continue

            self.value_before_conversion[name] = {}

            for key, values in collection.items():
                self.value_before_conversion[name][key] = {}

                pen = QPen(ColorPalette[color_index], 1.25, Qt.SolidLine,
                           Qt.SquareCap, Qt.MiterJoin)

                series = self.series[key] = QLineSeries()
                series.setName(
                    self.get_display_name(
                        database.definitions[name]['metadata'][key]))
                series.setMarkerSize(self.point_size)
                series.setPointsVisible(True)
                series.setPen(pen)

                for t, v in values.items():
                    timestamp = QDateTime(t.date(), t.time(),
                                          QTimeZone.utc()).toMSecsSinceEpoch()

                    if v in config.GUI.plots_mapping:
                        self.value_before_conversion[name][key][timestamp] = v
                        v = config.GUI.plots_mapping[v]

                    if v is None:
                        # TODO: interupt line
                        continue

                    if type(v) != int and type(v) != float:
                        continue

                    plot_min = min(plot_min, v)
                    plot_max = max(plot_max, v)

                    if name == 'obs' and series.count() > 0:
                        prev = series.points()[-1]
                        series.append(QPointF(timestamp, prev.y()))

                        series.setPointConfiguration(series.count() - 1, {
                            QXYSeries.PointConfiguration.Visibility: False
                        })

                    series.append(QPointF(timestamp, v))

                if name == 'obs' and series.count() > 0:
                    now = QDateTime.currentDateTime().toMSecsSinceEpoch()
                    prev = series.points()[-1]
                    if now > prev.x():
                        series.append(QPointF(now, prev.y()))

                        series.setPointConfiguration(series.count() - 1, {
                            QXYSeries.PointConfiguration.Visibility: False
                        })

                chart.addSeries(series)
                series.attachAxis(self.axis_x)
                series.attachAxis(self.axis_y)

                series.hovered.connect(lambda point, state, name=name, key=key:
                                       self.pointHoveredEvent(
                                           point, state, name, key))

                color_index = (color_index+1) % len(ColorPalette)

        time_delta = self.start_datetimeedit.dateTime().secsTo(
            self.end_datetimeedit.dateTime())
        if time_delta > 86400:
            self.axis_x.setFormat("HH:mm dd.MM.yy")
        else:
            self.axis_x.setFormat("HH:mm")

        delta = plot_max - plot_min
        if abs(delta) < config.epsilon:
            plot_min -= 0.01
            plot_max += 0.01
        else:
            plot_min -= 0.05 * delta
            plot_max += 0.05 * delta

        self.axis_x.setRange(self.start_datetimeedit.dateTime().toUTC(),
                             self.end_datetimeedit.dateTime().toUTC())
        self.axis_y.setRange(plot_min, plot_max)
        self.axis_y.setTickCount(20)
        self.axis_y.applyNiceNumbers()

        with QSignalBlocker(self.min_spinbox):
            self.min_spinbox.setMaximum(self.axis_y.max())
            self.min_spinbox.setValue(self.axis_y.min())

        with QSignalBlocker(self.max_spinbox):
            self.max_spinbox.setMinimum(self.axis_y.min())
            self.max_spinbox.setValue(self.axis_y.max())

    def hover_xy_to_str(self, x, y):
        if not np.isnan(x) and not np.isnan(y):
            metadata = database.definitions[self.current_name]['metadata'][
                self.current_key]

            try:
                y_true = f' ({self.value_before_conversion[self.current_name][self.current_key][x]})'
            except KeyError:
                y_true = ''

            x = QDateTime.fromMSecsSinceEpoch(
                int(x)).toString("HH:mm:ss dd-MM-yy")

            unit = kalao_string.get_unit_string(metadata)

            self.hovered.emit(
                f'{metadata["short"]}: {y:.5g}{unit}{y_true} at {x}')
        else:
            self.hovered.emit(f'')

    def pointHoveredEvent(self, point, state, name, key):
        self.current_name = name
        self.current_key = key

        self.plots_view.chart.pointHoveredEvent(point, state, self.series[key])

    def eventFilter(self, source, event):
        if isinstance(source, QListWidget):
            if event.type() == QEvent.Leave:
                self.hovered.emit('')
        return QObject.eventFilter(self, source, event)
