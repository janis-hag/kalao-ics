from datetime import datetime, timezone

import numpy as np

from PySide6.QtCharts import (QChartView, QDateTimeAxis, QLineSeries,
                              QValueAxis, QXYSeries)
from PySide6.QtCore import (QDateTime, QEvent, QObject, QPointF,
                            QSignalBlocker, QTimer, QTimeZone, Signal, Slot)
from PySide6.QtGui import QPen, Qt
from PySide6.QtWidgets import (QListWidget, QListWidgetItem, QMessageBox,
                               QPushButton)

from guis.utils.mixins import BackendActionMixin
from kalao import database
from kalao.utils import kstring, ktime

from guis.utils.definitions import ColorPalette
from guis.utils.ui_loader import loadUi
from guis.utils.widgets import KListWidgetItem, KMessageBox, KWidget

import config


class PlotsWidget(KWidget, BackendActionMixin):
    hovered = Signal(str)

    current_index = -1

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
            item = KListWidgetItem(k, self.get_display_name(v))
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
            item = KListWidgetItem(k, self.get_display_name(v))
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

            item = KListWidgetItem(k, self.get_display_name(v))
            item.hover_text = v['long']
            # item.installEventFilter(self)
            self.obs_list.addItem(item)

            self.items[f'obs/{k}'] = item
        self.obs_list.installEventFilter(self)

        # Create Chart and set General Chart setting
        chart = self.plots_view.chart()

        # X Axis Settings
        self.axis_x = QDateTimeAxis()
        self.axis_x.setTickCount(13)
        self.axis_x.setFormat("HH:mm")
        self.axis_x.setRange(self.since_datetimeedit.dateTime(),
                             self.until_datetimeedit.dateTime())
        chart.addAxis(self.axis_x, Qt.AlignBottom)

        # Y Axis Settings
        self.axis_y = QValueAxis()
        self.axis_y.setTickCount(20)
        self.axis_y.setRange(-1, 1)
        chart.addAxis(self.axis_y, Qt.AlignLeft)

        #chart.legend().hide()

        chart.hovered.connect(self.hover_xy_to_str)

        self.plots_view.setRubberBand(QChartView.RectangleRubberBand)

        ### Group buttons

        for group in sorted(self.groups.keys(),
                            key=lambda key: key.casefold()):
            button = QPushButton(group)
            button.clicked.connect(lambda checked=False, group=group: self.
                                   on_group_button_clicked(checked, group))
            self.group_layout.addWidget(button)

        self.live_timer = QTimer(parent=self)

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
    def on_since_datetimeedit_dateTimeChanged(self, datetime):
        self.until_datetimeedit.setMinimumDateTime(datetime)

        self.axis_x.setRange(self.since_datetimeedit.dateTime(),
                             self.until_datetimeedit.dateTime())

    @Slot(QDateTime)
    def on_until_datetimeedit_dateTimeChanged(self, datetime):
        self.since_datetimeedit.setMaximumDateTime(datetime)

        self.axis_x.setRange(self.since_datetimeedit.dateTime(),
                             self.until_datetimeedit.dateTime())

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
        until = QDateTime.currentDateTime()
        since = until.addSecs(-3600)

        self.since_datetimeedit.setDateTime(since)
        self.until_datetimeedit.setDateTime(until)

    @Slot(bool)
    def on_tonight_button_clicked(self, checked):
        start_of_night = ktime.get_start_of_night(datetime.now(timezone.utc))

        since = QDateTime.fromSecsSinceEpoch(int(start_of_night.timestamp()))
        until = since.addSecs(86400)

        self.since_datetimeedit.setDateTime(since)
        self.until_datetimeedit.setDateTime(until)

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
        time_delta = self.until_datetimeedit.dateTime().msecsTo(
            self.since_datetimeedit.dateTime())

        now = QDateTime.currentDateTime()
        prev = now.addMSecs(time_delta)

        self.until_datetimeedit.setDateTime(now)
        self.since_datetimeedit.setDateTime(prev)

        self.on_plot_button_clicked(None)

    @Slot(bool)
    def on_plot_button_clicked(self, checked):
        monitoring_keys = []
        telemetry_keys = []
        obs_keys = []

        for item in self.monitoring_list.selectedItems():
            monitoring_keys.append(item.key)

        for item in self.telemetry_list.selectedItems():
            telemetry_keys.append(item.key)

        for item in self.obs_list.selectedItems():
            obs_keys.append(item.key)

        since = self.since_datetimeedit.dateTime().toUTC().toPython().replace(
            tzinfo=timezone.utc)
        until = self.until_datetimeedit.dateTime().toUTC().toPython().replace(
            tzinfo=timezone.utc)

        # Gather plots data

        data = self.action_send(self.plot_button, self.backend.set_plots_data,
                                since=since, until=until,
                                monitoring_keys=monitoring_keys,
                                telemetry_keys=telemetry_keys,
                                obs_keys=obs_keys)

        # Display plots

        chart = self.plots_view.chart()

        chart.removeAllSeries()
        self.series = {}
        self.value_before_conversion = {}

        color_index = 0
        plot_min = np.inf
        plot_max = -np.inf

        no_data = True

        for name, collection in data.items():
            if collection.empty:
                continue

            no_data = False

            self.value_before_conversion[name] = {}

            for key, values in collection.items():
                self.value_before_conversion[name][key] = {}

                pen = QPen(ColorPalette[color_index], 1.25, Qt.SolidLine,
                           Qt.SquareCap, Qt.MiterJoin)

                series = self.series[key] = QLineSeries()
                series.setName(
                    self.get_display_name(
                        database.definitions[name]['metadata'][key]))
                series.setMarkerSize(chart.point_size)
                series.setPointsVisible(True)
                series.setPen(pen)

                for t, v in values.items():
                    t = t.astimezone(timezone.utc)
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
                    now = QDateTime.currentMSecsSinceEpoch()
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

        time_delta = self.since_datetimeedit.dateTime().secsTo(
            self.until_datetimeedit.dateTime())
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

        self.axis_x.setRange(self.since_datetimeedit.dateTime().toUTC(),
                             self.until_datetimeedit.dateTime().toUTC())
        self.axis_y.setRange(plot_min, plot_max)
        self.axis_y.setTickCount(20)
        self.axis_y.applyNiceNumbers()

        with QSignalBlocker(self.min_spinbox):
            self.min_spinbox.setMaximum(self.axis_y.max())
            self.min_spinbox.setValue(self.axis_y.min())

        with QSignalBlocker(self.max_spinbox):
            self.max_spinbox.setMinimum(self.axis_y.min())
            self.max_spinbox.setValue(self.axis_y.max())

        if no_data:
            msgbox = KMessageBox(self)
            msgbox.setIcon(QMessageBox.Critical)
            msgbox.setText("<b>No data!</b>")
            msgbox.setInformativeText(
                f'No data was found for the requested period of time and the requested series.'
            )
            msgbox.setModal(True)
            msgbox.show()

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

            unit = kstring.get_unit_string(metadata)

            self.hovered.emit(
                f'{metadata["short"]}: {y:.5g}{unit}{y_true} at {x}')
        else:
            self.hovered.emit(f'')

    def pointHoveredEvent(self, point, state, name, key):
        self.current_name = name
        self.current_key = key

        self.plots_view.chart().pointHoveredEvent(point, state,
                                                  self.series[key])

    def eventFilter(self, source, event):
        if isinstance(source, QListWidget):
            if event.type() == QEvent.Leave:
                self.hovered.emit('')
        return QObject.eventFilter(self, source, event)
