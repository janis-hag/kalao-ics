from typing import Any

import numpy as np

from PySide6.QtCore import QRectF, QTimer, Slot
from PySide6.QtGui import (QBrush, QCloseEvent, QColor, QFont, QPainter, QPen,
                           QResizeEvent, QShowEvent, Qt)
from PySide6.QtWidgets import QWidget

from compiled.ui_spiral_search import Ui_SpiralSearchWindow

from kalao.sequencer import centering
from kalao.utils import kstring
from kalao.utils.json import KalAOJSONDecoder

from kalao.guis.backends.abstract import AbstractBackend
from kalao.guis.utils.definitions import Color
from kalao.guis.utils.mixins import BackendDataMixin
from kalao.guis.utils.widgets import (CenteredTextItem,
                                      KHoverableGraphicsScene, KMainWindow)

import config

decoder = KalAOJSONDecoder()


class SpiralSearchWindow(KMainWindow, BackendDataMixin):
    _view = QRectF(0, 0, 1, 1)

    star_x = np.nan
    star_y = np.nan

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

        self.ui.spiral_search_view.setRenderHints(
            QPainter.RenderHint.Antialiasing |
            QPainter.RenderHint.SmoothPixmapTransform)

        self.ui.area_label.updateText(x='--"', y='--"')
        self.ui.star_label.updateText(text='--')

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
            self.star_x = spiral_search['star_x']
            self.star_y = spiral_search['star_y']
            self.expno = spiral_search['expno']

            if self.star_x is None:
                self.star_x = np.nan

            if self.star_y is None:
                self.star_y = np.nan

            self.ui.overlap_spinbox.setValue(
                round(spiral_search['overlap'] * 100))
            self.ui.radius_spinbox.setValue(spiral_search['radius'] + 1)

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

        self.ui.area_label.updateText(
            x=kstring.sec_to_dms_str(area_x * config.Camera.plate_scale),
            y=kstring.sec_to_dms_str(area_y * config.Camera.plate_scale))

        # Compute coords

        coords = centering.spiral_create_grid(overlap=overlap, radius=radius)

        # Default pen and brush

        pen = QPen(Color.GREY, 1.5, Qt.PenStyle.SolidLine,
                   Qt.PenCapStyle.SquareCap, Qt.PenJoinStyle.MiterJoin)
        pen.setCosmetic(True)

        brush = QBrush(
            QColor(Color.GREY.red(), Color.GREY.green(), Color.GREY.blue(),
                   16), Qt.BrushStyle.SolidPattern)

        font = QFont()
        font.setPixelSize(256)
        font.setBold(True)
        brush_font = QBrush(Color.GREY, Qt.BrushStyle.SolidPattern)

        # Pen and brush for exposures done

        pen_done = QPen(Color.GREEN, 1.5, Qt.PenStyle.SolidLine,
                        Qt.PenCapStyle.SquareCap, Qt.PenJoinStyle.MiterJoin)
        pen_done.setCosmetic(True)

        brush_done = QBrush(
            QColor(Color.GREEN.red(), Color.GREEN.green(), Color.GREEN.blue(),
                   32))

        # Draw detector footprints

        for i, coord in enumerate(coords):
            rect = QRectF(coord.x - config.Camera.size_x / 2,
                          coord.y - config.Camera.size_y / 2,
                          config.Camera.size_x, config.Camera.size_y)
            rect_item = self._scene.addRect(rect, pen, brush)

            if i <= self.expno:
                rect_item.setPen(pen_done)
                rect_item.setBrush(brush_done)
                rect_item.setZValue(100)

            # Draw footprint index

            text_item = CenteredTextItem(f'{i}')
            text_item.setFont(font)
            text_item.setPos(coord.x, coord.y)
            text_item.setBrush(brush_font)
            self._scene.addItem(text_item)
            text_item.setZValue(200)

        # Draw star if found

        pen_star = QPen(Color.RED, 1.5, Qt.PenStyle.SolidLine,
                        Qt.PenCapStyle.SquareCap, Qt.PenJoinStyle.MiterJoin)
        pen_star.setCosmetic(True)

        if not np.isnan(self.star_x) and not np.isnan(self.star_y):
            self._scene.addLine(self.star_x - 50, self.star_y - 50,
                                self.star_x + 50, self.star_y + 50,
                                pen_star).setZValue(300)
            self._scene.addLine(self.star_x + 50, self.star_y - 50,
                                self.star_x - 50, self.star_y + 50,
                                pen_star).setZValue(300)

            self.ui.star_label.updateText(
                text=
                f'alt = {+self.star_x*config.Offsets.camera_x_to_tel_alt:.2f}" and az = {+self.star_y*config.Offsets.camera_y_to_tel_az:.2f}"'
            )
        else:
            self.ui.star_label.updateText(text='not found')

        # Update view

        self._view = QRectF(-0.5 * area_x, -0.5 * area_y, area_x, area_y)

        self._scene.setSceneRect(self._view)
        self.ui.spiral_search_view.fitInView(self._view,
                                       Qt.AspectRatioMode.KeepAspectRatio)

    def resizeEvent(self, event: QResizeEvent) -> None:
        self.ui.spiral_search_view.fitInView(self._view,
                                       Qt.AspectRatioMode.KeepAspectRatio)

        return super().resizeEvent(event)

    def closeEvent(self, event: QCloseEvent) -> None:
        self.spiral_timer.stop()

        return super().closeEvent(event)

    def showEvent(self, event: QShowEvent) -> None:
        if not event.spontaneous():
            self.ui.spiral_search_view.fitInView(self._view,
                                           Qt.AspectRatioMode.KeepAspectRatio)

        QTimer.singleShot(0, self.backend, self.backend.centering_spiral_data)

        self.spiral_timer.start()

        return super().showEvent(event)
