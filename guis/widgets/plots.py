from datetime import datetime, timezone

import numpy as np
import pandas as pd

from PySide6.QtCharts import QChartView, QDateTimeAxis, QLineSeries, QValueAxis
from PySide6.QtCore import (QDateTime, QEvent, QObject, QPointF, QTimer,
                            Signal, Slot)
from PySide6.QtGui import QPen, Qt
from PySide6.QtWidgets import QMessageBox, QTreeWidgetItem

from kalao import database
from kalao.utils import kstring, ktime

from guis.utils.definitions import Color, ColorPalette
from guis.utils.mixins import BackendActionMixin
from guis.utils.ui_loader import loadUi
from guis.utils.widgets import KMessageBox, KWidget

import config


class PlotsWidget(KWidget, BackendActionMixin):
    hovered = Signal(str)

    activeToolTip = None

    def __init__(self, backend, parent=None):
        super().__init__(parent)

        self.backend = backend

        loadUi('plots.ui', self)
        self.resize(600, 400)

        self.groups = {}
        self.items = {}

        for collection_name, item_list in [('monitoring',
                                            self.monitoring_treeview),
                                           ('obs', self.obs_treeview)]:
            for k, v in sorted(
                    database.definitions[collection_name]['metadata'].items(),
                    key=lambda t:
                (t[1].get('group', ''), t[1]['short'].casefold())):
                if k in config.GUI.plots_exclude_list:
                    continue

                item = QTreeWidgetItem([v['short']])
                item.setCheckState(0, Qt.Unchecked)
                item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                item.setToolTip(0, v['long'])
                item.key = k

                group = v.get('group')
                group_key = f'{collection_name}/{group}'
                if group is None:
                    item_list.addTopLevelItem(item)
                elif group_key not in self.groups:
                    group_item = self.groups[group_key] = QTreeWidgetItem([
                        group
                    ])
                    item_list.addTopLevelItem(group_item)
                    group_item.setFlags(Qt.ItemIsUserCheckable |
                                        Qt.ItemIsEnabled |
                                        Qt.ItemIsAutoTristate)
                    group_item.setExpanded(True)
                    group_item.key = group
                else:
                    group_item = self.groups[group_key]

                group_item.addChild(item)

                self.items[f'{collection_name}/{k}'] = item
            item_list.installEventFilter(self)

        # Create Chart and set General Chart setting
        chart = self.plots_view.chart()

        # X Axis Settings
        self.axis_x = QDateTimeAxis()
        self.axis_x.setTickCount(13)
        self.axis_x.setFormat('HH:mm')
        self.axis_x.setRange(self.since_datetimeedit.dateTime(),
                             self.until_datetimeedit.dateTime())
        chart.addAxis(self.axis_x, Qt.AlignBottom)

        self.axis_x.rangeChanged.connect(self.x_range_changed)

        # Y Axis Settings
        self.axis_y = QValueAxis()
        self.axis_y.setTickCount(20)
        self.axis_y.setRange(-1, 1)
        chart.addAxis(self.axis_y, Qt.AlignLeft)

        self.axis_y.rangeChanged.connect(self.y_range_changed)

        #chart.legend().hide()

        chart.hovered.connect(self.hover_xy_to_str)

        self.plots_view.setRubberBand(QChartView.RectangleRubberBand)

        self.autoupdate_timer = QTimer(parent=self)

        self.on_tonight_button_clicked(None)
        self.on_autoupdate_database_button_toggled(
            self.autoupdate_database_button.isChecked())

    def get_display_name(self, metadata):
        unit = metadata.get('unit')
        if unit is None or unit == '':
            unit = ' [-]'
        else:
            unit = f' [{unit}]'

        return f'{metadata["short"]}{unit}'

    @Slot(bool)
    def on_reset_all_button_clicked(self, checked):
        for item in self.monitoring_treeview.findItems(
                '', Qt.MatchContains | Qt.MatchRecursive):
            item.setCheckState(0, Qt.Unchecked)

        for item in self.obs_treeview.findItems(
                '', Qt.MatchContains | Qt.MatchRecursive):
            item.setCheckState(0, Qt.Unchecked)

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
    def on_last_5minutes_button_clicked(self, checked):
        until = QDateTime.currentDateTime()
        since = until.addSecs(-300)

        self.since_datetimeedit.setDateTime(since)
        self.until_datetimeedit.setDateTime(until)

    @Slot(bool)
    def on_last_hour_button_clicked(self, checked):
        until = QDateTime.currentDateTime()
        since = until.addSecs(-3600)

        self.since_datetimeedit.setDateTime(since)
        self.until_datetimeedit.setDateTime(until)

    @Slot(bool)
    def on_last_day_button_clicked(self, checked):
        until = QDateTime.currentDateTime()
        since = until.addSecs(-86400)

        self.since_datetimeedit.setDateTime(since)
        self.until_datetimeedit.setDateTime(until)

    @Slot(bool)
    def on_last_week_button_clicked(self, checked):
        until = QDateTime.currentDateTime()
        since = until.addSecs(-604800)

        self.since_datetimeedit.setDateTime(since)
        self.until_datetimeedit.setDateTime(until)

    @Slot(bool)
    def on_last_month_button_clicked(self, checked):
        until = QDateTime.currentDateTime()
        since = until.addSecs(-18144000)

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
    def on_autoupdate_checkbox_stateChanged(self, state):
        if Qt.CheckState(state) == Qt.Checked:
            self.autoupdate_df = None

            self.plot_button.setEnabledStack(False, 'autoupdate')

            self.autoupdate_timer.timeout.connect(
                self.on_autoupdate_timer_timeout)

            self.on_autoupdate_timer_timeout()
            self.autoupdate_timer.start()
        else:
            self.plot_button.setEnabledStack(True, 'autoupdate')

            self.autoupdate_timer.stop()

    @Slot(bool)
    def on_autoupdate_database_button_toggled(self, checked):
        if checked:
            self.autoupdate_timer.setInterval(
                int(1000 * config.Monitoring.update_interval))
            self.autoupdate_refresh_rate_spinbox.setEnabled(False)
        else:
            self.autoupdate_timer.setInterval(
                int(1000 * self.autoupdate_refresh_rate_spinbox.value()))
            self.autoupdate_refresh_rate_spinbox.setEnabled(True)

    @Slot(float)
    def on_autoupdate_refresh_rate_spinbox_valueChanged(self, d):
        self.autoupdate_timer.setInterval(int(1000 * d))

    def on_autoupdate_timer_timeout(self):
        time_delta = self.until_datetimeedit.dateTime().msecsTo(
            self.since_datetimeedit.dateTime())

        now = QDateTime.currentDateTime()
        prev = now.addMSecs(time_delta)

        self.until_datetimeedit.setDateTime(now)
        self.since_datetimeedit.setDateTime(prev)

        if self.autoupdate_database_button.isChecked():
            self.on_plot_button_clicked(None)
        else:
            data = self.action_send([], self.backend.plots_data_live)

            monitoring_keys = []
            for item in self.monitoring_treeview.findItems(
                    '', Qt.MatchContains | Qt.MatchRecursive):
                if item.checkState(0) == Qt.Checked and item.childCount() == 0:
                    monitoring_keys.append(item.key)

            timestamp = data['timestamp']
            del data['timestamp']

            row = pd.DataFrame.from_records([data], index=[timestamp])

            if self.autoupdate_df is None:
                self.autoupdate_df = row
            else:
                self.autoupdate_df = pd.concat([self.autoupdate_df, row])

            self.plot_data({'monitoring': self.autoupdate_df[monitoring_keys]})

    @Slot(bool)
    def on_plot_button_clicked(self, checked):
        monitoring_keys = []
        obs_keys = []

        for item in self.monitoring_treeview.findItems(
                '', Qt.MatchContains | Qt.MatchRecursive):
            if item.checkState(0) == Qt.Checked and item.childCount() == 0:
                monitoring_keys.append(item.key)

        for item in self.obs_treeview.findItems(
                '', Qt.MatchContains | Qt.MatchRecursive):
            if item.checkState(0) == Qt.Checked and item.childCount() == 0:
                obs_keys.append(item.key)

        series_to_draw = len(monitoring_keys) + len(obs_keys)

        if series_to_draw == 0 and not self.autoupdate_timer.isActive():
            msgbox = KMessageBox(self)
            msgbox.setIcon(QMessageBox.Critical)
            msgbox.setText('<b>No series selected!</b>')
            msgbox.setInformativeText('Please select at least one series.')
            msgbox.setModal(True)
            msgbox.show()
            return

        since = self.since_datetimeedit.dateTime().toUTC().toPython().replace(
            tzinfo=timezone.utc)
        until = self.until_datetimeedit.dateTime().toUTC().toPython().replace(
            tzinfo=timezone.utc)

        # Gather plots data

        data = self.action_send(self.plot_button, self.backend.plots_data_db,
                                since=since, until=until,
                                monitoring_keys=monitoring_keys,
                                obs_keys=obs_keys)

        # Display plots
        self.plot_data(data)

    def plot_data(self, data):
        chart = self.plots_view.chart()

        chart.removeAllSeries()
        self.series = {}
        self.value_before_conversion = {}

        color_index = 0
        plot_min = np.inf
        plot_max = -np.inf

        no_data = True

        self.plots_view.resetHLines()

        for collection_name, collection in data.items():
            if collection.empty:
                continue

            no_data = False

            self.value_before_conversion[collection_name] = {}

            for series_name, series_values in collection.items():
                self.value_before_conversion[collection_name][series_name] = {}

                metadata = database.definitions[collection_name]['metadata'][
                    series_name]

                pen = QPen(ColorPalette[color_index], 1.25, Qt.SolidLine,
                           Qt.SquareCap, Qt.MiterJoin)

                series = self.series[series_name] = QLineSeries()
                series.setName(self.get_display_name(metadata))
                series.setPen(pen)

                points = []

                if config.GUI.opengl_charts:
                    series.setUseOpenGL(True)

                if len(self.series) == 1:
                    alarm_range = metadata.get('alarm_range', [np.nan, np.nan])
                    warn_range = metadata.get('warn_range', [np.nan, np.nan])

                    error_min = alarm_range[0]
                    error_max = alarm_range[1]
                    warn_min = warn_range[0]
                    warn_max = warn_range[1]

                    if not np.isnan(error_min):
                        self.plots_view.addHLine(error_min, Color.RED)
                    if not np.isnan(error_max):
                        self.plots_view.addHLine(error_max, Color.RED)
                    if not np.isnan(warn_min):
                        self.plots_view.addHLine(warn_min, Color.ORANGE)
                    if not np.isnan(warn_max):
                        self.plots_view.addHLine(warn_max, Color.ORANGE)
                else:
                    self.plots_view.resetHLines()

                for t, v in series_values.items():
                    timestamp_msec = int(t.timestamp() * 1000)

                    if v in config.GUI.plots_mapping:
                        self.value_before_conversion[collection_name][
                            series_name][timestamp_msec] = v
                        v = config.GUI.plots_mapping[v]

                    if v is None or np.isnan(v) or np.isinf(v):
                        # TODO: interupt line
                        continue

                    if not isinstance(v, int) and not isinstance(v, float):
                        continue

                    plot_min = min(plot_min, v)
                    plot_max = max(plot_max, v)

                    # Create a "staircase" effect
                    if collection_name == 'obs' and len(points) > 0:
                        prev = points[-1]
                        points.append(QPointF(timestamp_msec, prev.y()))

                    points.append(QPointF(timestamp_msec, v))

                if collection_name == 'obs' and series.count() > 0:
                    now = QDateTime.currentMSecsSinceEpoch()
                    prev = points[-1]
                    if now > prev.x():
                        points.append(QPointF(now, prev.y()))

                series.replace(points)

                chart.addSeries(series)
                series.attachAxis(self.axis_x)
                series.attachAxis(self.axis_y)

                series.hovered.connect(
                    lambda point, state, collection_name=collection_name,
                    series_name=series_name: self.pointHoveredEvent(
                        point, state, collection_name, series_name))

                color_index = (color_index+1) % len(ColorPalette)

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

        if no_data and not self.autoupdate_timer.isActive():
            msgbox = KMessageBox(self)
            msgbox.setIcon(QMessageBox.Critical)
            msgbox.setText('<b>No data!</b>')
            msgbox.setInformativeText(
                'No data was found for the requested period of time and the requested series.'
            )
            msgbox.setModal(True)
            msgbox.show()

    def x_range_changed(self, min, max):
        self.since_datetimeedit.setDateTime(min)
        self.until_datetimeedit.setDateTime(max)

        time_delta = min.secsTo(max)

        if time_delta > 86400 * 365:
            self.axis_x.setFormat('HH:mm dd.MM.yy')
        elif time_delta > 86400:
            self.axis_x.setFormat('HH:mm dd.MM')
        elif time_delta > 3600:
            self.axis_x.setFormat('HH:mm')
        else:
            self.axis_x.setFormat('HH:mm:ss')

    def y_range_changed(self, min, max):
        self.min_spinbox.setValue(min)
        self.max_spinbox.setValue(max)

    def hover_xy_to_str(self, series, x, y):
        if not np.isnan(x) and not np.isnan(y):
            x = QDateTime.fromMSecsSinceEpoch(
                int(x)).toString('HH:mm:ss dd-MM-yy')

            if series is None:
                self.hovered.emit(f'{y:.9g} at {x}')
            else:
                metadata = database.definitions[
                    self.current_collection]['metadata'][self.current_series]

                try:
                    y_true = f' ({self.value_before_conversion[self.current_collection][self.current_series][x]})'
                except KeyError:
                    y_true = ''

                unit = kstring.get_unit_string(metadata)

                self.hovered.emit(
                    f'{metadata["short"]}: {y:.9g}{unit}{y_true} at {x}')
        else:
            self.hovered.emit('')

    def pointHoveredEvent(self, point, state, collection, series):
        self.current_collection = collection
        self.current_series = series

        self.plots_view.chart().pointHoveredEvent(point, state,
                                                  self.series[series])

    @Slot(QTreeWidgetItem, int)
    def on_monitoring_treeview_itemEntered(self, item, column):
        self.hovered.emit(item.toolTip(0))

    @Slot(QTreeWidgetItem, int)
    def on_obs_treeview_itemEntered(self, item, column):
        self.hovered.emit(item.toolTip(0))

    def eventFilter(self, source, event):
        if isinstance(source,
                      QTreeWidgetItem) and event.type() == QEvent.Leave:
            self.hovered.emit('')

        return QObject.eventFilter(self, source, event)
