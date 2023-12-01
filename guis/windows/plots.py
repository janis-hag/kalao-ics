from datetime import datetime, timedelta, timezone

import numpy as np

from PySide6.QtCharts import QDateTimeAxis, QLineSeries, QValueAxis, QXYSeries
from PySide6.QtCore import QDateTime, QPointF, Qt, QTimeZone, Signal, Slot

from kalao.utils import database, kalao_time

from guis.kalao.ui_loader import loadUi
from guis.kalao.widgets import KalAOListWidgetItem, KalAOWidget

import config


class PlotsWidget(KalAOWidget):
    hovered = Signal(str)
    point_size = 3

    current_index = -1

    def __init__(self, backend, parent=None):
        super().__init__(parent)

        self.backend = backend

        loadUi('plots.ui', self)
        self.resize(600, 400)

        start = kalao_time.get_start_of_night_dt(kalao_time.now())

        self.start_datetimeedit.setDateTime(start)
        self.end_datetimeedit.setDateTime(start + timedelta(hours=24))

        for k, v in sorted(
                database.definitions['monitoring']['metadata'].items(),
                key=lambda t: t[1]['short']):
            item = KalAOListWidgetItem(k, self.get_display_name(v))
            item.setToolTip(v['long'])
            self.monitoring_list.addItem(item)

        for k, v in sorted(
                database.definitions['telemetry']['metadata'].items(),
                key=lambda t: t[1]['short']):
            item = KalAOListWidgetItem(k, self.get_display_name(v))
            item.setToolTip(v['long'])
            self.telemetry_list.addItem(item)

        # Create Chart and set General Chart setting
        chart = self.plots_view.chart

        # X Axis Settings
        self.axisX = QDateTimeAxis()
        self.axisX.setTickCount(13)
        self.axisX.setFormat("yy-MM-dd HH:mm")
        self.axisX.setRange(self.start_datetimeedit.dateTime(),
                            self.end_datetimeedit.dateTime())
        chart.addAxis(self.axisX, Qt.AlignBottom)

        # Y Axis Settings
        self.axisY = QValueAxis()
        self.axisY.setTickCount(5)
        self.axisY.setRange(-1, 1)
        chart.addAxis(self.axisY, Qt.AlignLeft)

        #chart.legend().hide()

    def get_display_name(self, metadata):
        unit = metadata.get("unit")
        if unit is None or unit == '':
            unit = ' [-]'
        else:
            unit = f' [{unit}]'

        return f'{metadata["short"]}{unit}'

    @Slot(bool)
    def on_plot_button_clicked(self, checked):
        monitoring_keys = []
        telemetry_keys = []

        for item in self.monitoring_list.selectedItems():
            monitoring_keys.append(item.key)

        for item in self.telemetry_list.selectedItems():
            telemetry_keys.append(item.key)

        dt_start = self.start_datetimeedit.dateTime().toUTC().toPython()
        dt_end = self.end_datetimeedit.dateTime().toUTC().toPython()

        dt_start = dt_start.replace(tzinfo=timezone.utc)
        dt_end = dt_end.replace(tzinfo=timezone.utc)

        data = self.backend.get_plots_data(dt_start, dt_end, monitoring_keys,
                                           telemetry_keys)

        chart = self.plots_view.chart

        chart.removeAllSeries()
        self.series = {}

        plot_min = np.inf
        plot_max = -np.inf

        for name, collection in data.items():
            if collection.empty:
                continue

            for key, values in collection.items():
                series = self.series[key] = QLineSeries()
                series.setName(
                    self.get_display_name(
                        database.definitions[name]['metadata'][key]))

                #TODO: if values is a string
                plot_min = min(plot_min, values.min())
                plot_max = max(plot_max, values.max())

                for t, v in values.items():
                    timestamp = QDateTime(t.date(), t.time(),
                                          QTimeZone.utc()).toMSecsSinceEpoch()

                    if v in config.GUI.plots_map_to_0:
                        v = 0
                    elif v in config.GUI.plots_map_to_1:
                        v = 1

                    #TODO: behavior with None

                    series.append(QPointF(timestamp, v))

                series.setMarkerSize(self.point_size)
                series.setPointsVisible(True)

                chart.addSeries(series)
                series.attachAxis(self.axisX)
                series.attachAxis(self.axisY)

                series.hovered.connect(lambda point, state, name=name, key=key:
                                       self.point_hovered(
                                           point, state, name, key))

        self.axisX.setRange(self.start_datetimeedit.dateTime().toUTC(),
                            self.end_datetimeedit.dateTime().toUTC())
        self.axisY.setRange(plot_min, plot_max)

    def point_hovered(self, point, state, name, key):
        points = self.series[key].points()

        closest_point, closest_index = self.find_closest_point(point, points)

        metadata = database.definitions[name]['metadata'][key]

        if self.current_index != -1:
            self.series[key].setPointConfiguration(self.current_index, {
                QXYSeries.PointConfiguration.Size: self.point_size
            })

        if state:
            self.series[key].setPointConfiguration(closest_index, {
                QXYSeries.PointConfiguration.Size: 2 * self.point_size
            })

            x = QDateTime.fromMSecsSinceEpoch(int(
                closest_point.x())).toString("HH:mm:ss dd-MM-yy")

            self.hovered.emit(
                f'{metadata["short"]}: {closest_point.y():.5g} {metadata["unit"]} at {x}')
        else:
            self.series[key].setPointConfiguration(closest_index, {
                QXYSeries.PointConfiguration.Size: self.point_size
            })

            self.hovered.emit('')

        self.current_index = closest_index

    def find_closest_point(self, point, points):
        closest_point = min(points, key=lambda p: self.points_distance(p, point))
        closest_index = points.index(closest_point)

        return closest_point, closest_index

    def points_distance(self, point1, point2):
        diff = point2 - point1
        x = diff.x() / (self.axisX.max().toMSecsSinceEpoch() - self.axisX.min().toMSecsSinceEpoch())
        y = diff.y() / (self.axisY.max() - self.axisY.min())

        return x**2 + y **2
