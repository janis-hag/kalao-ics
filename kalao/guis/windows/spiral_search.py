from typing import Any

import numpy as np

from PySide6.QtCore import QPointF, QRectF, QTimer, Slot
from PySide6.QtGui import (QBrush, QCloseEvent, QColor, QFont, QPainter, QPen,
                           QPolygonF, QResizeEvent, QShowEvent, Qt)
from PySide6.QtWidgets import QWidget

from compiled.ui_spiral_search import Ui_SpiralSearchWindow

from kalao.common import spiral_search
from kalao.common.json import KalAOJSONDecoder

from kalao.guis.backends.abstract import AbstractBackend
from kalao.guis.utils.definitions import Color
from kalao.guis.utils.mixins import BackendActionMixin, BackendDataMixin
from kalao.guis.utils.widgets import (CenteredTextItem,
                                      KHoverableGraphicsScene, KMainWindow)

import config

decoder = KalAOJSONDecoder()


class SpiralSearchWindow(KMainWindow, BackendDataMixin, BackendActionMixin):
    _view = QRectF(0, 0, 1, 1)

    star_dx = np.nan
    star_dy = np.nan

    expno = 0

    def __init__(self, backend: AbstractBackend,
                 parent: QWidget = None) -> None:
        super().__init__(parent)

        self.backend = backend

        self.ui = Ui_SpiralSearchWindow()
        self.ui.setupUi(self)

        self.resize(600, 600)

        self._scene = KHoverableGraphicsScene()
        self.ui.spiral_search_view.setScene(self._scene)

        self.ui.spiral_search_view.setStyleSheet('background: transparent')
        self.ui.spiral_search_view.setBackgroundBrush(QBrush(
            Color.TRANSPARENT))

        self.ui.spiral_search_view.setRenderHints(
            QPainter.RenderHint.Antialiasing |
            QPainter.RenderHint.SmoothPixmapTransform)

        backend.centering_spiral_data_updated.connect(
            self.centering_spiral_data_updated)

        self.spiral_timer = QTimer(parent=self)
        self.spiral_timer.setInterval(
            int(1000 / config.GUI.refreshrate_auxillary))
        self.spiral_timer.timeout.connect(backend.centering_spiral_data)
        self.spiral_timer.start()

        self.show()
        self.center()

    def centering_spiral_data_updated(self, data: dict[str, Any]) -> None:
        spiral_search = self.consume_dict(data, 'memory', 'spiral_search')

        if spiral_search is not None:
            self.star_dx = spiral_search['star_dx']
            self.star_dy = spiral_search['star_dy']
            self.expno = spiral_search['expno']

            if self.star_dx is None:
                self.star_dx = np.nan

            if self.star_dy is None:
                self.star_dy = np.nan

            self.ui.overlap_spinbox.setValue(
                round(spiral_search['overlap'] * 100))
            self.ui.radius_spinbox.setValue(spiral_search['radius'] + 1)

            self.draw_grid()

    @Slot(int)
    def on_overlap_spinbox_valueChanged(self, i: int) -> None:
        self.draw_grid()

    @Slot(int)
    def on_radius_spinbox_valueChanged(self, i: int) -> None:
        self.draw_grid()

    def draw_grid(self):
        overlap = self.ui.overlap_spinbox.value() / 100
        radius = self.ui.radius_spinbox.value()

        # Clean scene

        for item in self._scene.items():
            self._scene.removeItem(item)

        # Compute area to be displayed

        area = (2*radius + 1) * (1-overlap) + overlap
        area_x = area * config.Camera.size_x
        area_y = area * config.Camera.size_x

        # Compute coords

        coords = spiral_search.generate_grid(overlap=overlap, radius=radius)

        # Default pen and brush

        pen = QPen(Color.GREY, 0.5, Qt.PenStyle.SolidLine,
                   Qt.PenCapStyle.SquareCap, Qt.PenJoinStyle.MiterJoin)
        pen.setCosmetic(True)

        brush = QBrush(
            QColor(Color.GREY.red(), Color.GREY.green(), Color.GREY.blue(),
                   48), Qt.BrushStyle.SolidPattern)

        font = QFont()
        font.setPixelSize(256)
        font.setBold(True)
        brush_font = QBrush(Color.GREY, Qt.BrushStyle.SolidPattern)

        # Pen and brush for exposures done

        pen_done = QPen(Color.GREEN, 0.5, Qt.PenStyle.SolidLine,
                        Qt.PenCapStyle.SquareCap, Qt.PenJoinStyle.MiterJoin)
        pen_done.setCosmetic(True)

        brush_done = QBrush(
            QColor(Color.GREEN.red(), Color.GREEN.green(), Color.GREEN.blue(),
                   64))

        # Draw detector footprints

        for i, coord in enumerate(coords):
            rect = QRectF(-coord.dx - config.Camera.size_x / 2,
                          -coord.dy - config.Camera.size_y / 2,
                          config.Camera.size_x, config.Camera.size_y)
            rect_item = self._scene.addRect(rect, pen, brush)

            if i <= self.expno:
                rect_item.setPen(pen_done)
                rect_item.setBrush(brush_done)
                rect_item.setZValue(100)

            # Draw footprint index

            text_item = CenteredTextItem(f'{i}')
            text_item.setFont(font)
            text_item.setPos(-coord.dx, -coord.dy)
            text_item.setBrush(brush_font)
            self._scene.addItem(text_item)
            text_item.setZValue(200)

        # Draw star if found
        brush_star = QBrush(Color.YELLOW, Qt.BrushStyle.SolidPattern)

        if not np.isnan(self.star_dx) and not np.isnan(self.star_dy):
            star = self._draw_star()

            star_item = self._scene.addPolygon(star, Qt.PenStyle.NoPen,
                                               brush_star)
            star_item.setPos(-self.star_dx, -self.star_dy)
            star_item.setZValue(300)

            self.ui.star_altitude_spinbox.setValue(
                self.star_dx * config.Offsets.camera_x_to_tel_alt)
            self.ui.star_azimut_spinbox.setValue(
                self.star_dy * config.Offsets.camera_y_to_tel_az)
        else:
            self.ui.star_altitude_spinbox.setValue(np.nan)
            self.ui.star_azimut_spinbox.setValue(np.nan)

        # Update view

        self._view = QRectF(-0.5 * area_x, -0.5 * area_y, area_x, area_y)

        self._scene.setSceneRect(self._view)
        self.ui.spiral_search_view.fitInView(
            self._view, Qt.AspectRatioMode.KeepAspectRatio)

    def _draw_star(self, size=100, branches=5) -> QPolygonF:
        polygon = QPolygonF()
        angle = 2 * np.pi / (2*branches)

        for i in range(branches):
            polygon.append(
                QPointF(-np.sin(2 * i * angle) * size,
                        -np.cos(2 * i * angle) * size))
            polygon.append(
                QPointF(-np.sin((2*i + 1) * angle) * size / 2, -np.cos(
                    (2*i + 1) * angle) * size / 2))
        polygon.append(QPointF(0, -size))

        return polygon

    @Slot(bool)
    def on_abort_button_clicked(self, checked: bool) -> None:
        self.action_send(self.ui.abort_button, self.backend.sequencer_abort)

    def resizeEvent(self, event: QResizeEvent) -> None:
        self.ui.spiral_search_view.fitInView(
            self._view, Qt.AspectRatioMode.KeepAspectRatio)

        return super().resizeEvent(event)

    def closeEvent(self, event: QCloseEvent) -> None:
        self.spiral_timer.stop()

        return super().closeEvent(event)

    def showEvent(self, event: QShowEvent) -> None:
        if not event.spontaneous():
            self.ui.spiral_search_view.fitInView(
                self._view, Qt.AspectRatioMode.KeepAspectRatio)

        QTimer.singleShot(0, self.backend, self.backend.centering_spiral_data)

        self.spiral_timer.start()

        return super().showEvent(event)
