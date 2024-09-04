import math
from typing import Any, Type

import numpy as np

from PySide6.QtCharts import (QAbstractAxis, QAbstractSeries, QChart,
                              QChartView, QDateTimeAxis, QXYSeries)
from PySide6.QtCore import (QEvent, QLineF, QMargins, QPoint, QPointF, QRect,
                            QRectF, QSignalBlocker, QSize, Signal)
from PySide6.QtGui import (QBrush, QCloseEvent, QColor, QFont, QIcon, QImage,
                           QMouseEvent, QPainter, QPainterPath, QPen, QPixmap,
                           QPolygonF, QResizeEvent, QSurfaceFormat, Qt,
                           QTransform)
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import (QAbstractSpinBox, QDateTimeEdit, QDoubleSpinBox,
                               QGraphicsItem, QGraphicsLineItem,
                               QGraphicsPixmapItem, QGraphicsRectItem,
                               QGraphicsScene, QGraphicsSimpleTextItem,
                               QGraphicsView, QLabel, QMainWindow, QMessageBox,
                               QSizePolicy, QSpacerItem,
                               QStyleOptionGraphicsItem, QWidget)

from kalao.common.image import AbstractScale, LinearScale

from kalao.guis.utils import colormaps, data_conversion
from kalao.guis.utils.colormaps import Colormap
from kalao.guis.utils.definitions import Color
from kalao.guis.utils.string_formatter import KalAOFormatter

import config


class KNoAALine(QGraphicsLineItem):
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem,
              widget: QWidget) -> None:
        painter.save()
        painter.setRenderHints(QPainter.RenderHint.Antialiasing, on=False)
        super().paint(painter, option, widget)
        painter.restore()


class KNoAARect(QGraphicsRectItem):
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem,
              widget: QWidget) -> None:
        painter.save()
        painter.setRenderHints(QPainter.RenderHint.Antialiasing, on=False)
        super().paint(painter, option, widget)
        painter.restore()


class OffsetedTextItem(QGraphicsSimpleTextItem):
    offset_x = 0
    offset_y = 0

    def setOffset(self, x: float, y: float) -> None:
        self.offset_x = x
        self.offset_y = y

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem,
              widget: QWidget) -> None:
        painter.translate(self.boundingRect().topLeft())
        super().paint(painter, option, widget)
        painter.translate(-self.boundingRect().topLeft())

    def boundingRect(self) -> QRectF:
        b = super().boundingRect()
        return QRectF(b.x() + self.offset_x,
                      b.y() + self.offset_y, b.width(), b.height())


class CenteredTextItem(QGraphicsSimpleTextItem):
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem,
              widget: QWidget) -> None:
        translation = QPointF(-self.boundingRect().width() / 2,
                              -self.boundingRect().height() / 2)
        painter.translate(translation)
        super().paint(painter, option, widget)
        painter.translate(-translation)


class KLabel(QLabel):
    _pixmap = None
    text_format = None
    formatter = KalAOFormatter()

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        if len(args) > 0 and isinstance(args[0], str):
            self.text_format = args[0]

    def setPixmap(self, p: QPixmap) -> None:
        self._pixmap = p
        super().setPixmap(self.scaled_pixmap())

    def heightForWidth(self, width: int) -> int:
        if self._pixmap is None:
            super().heightForWidth(width)
        else:
            return round(self._pixmap.height() * width / self._pixmap.width())

    def sizeHint(self) -> QSize:
        if self._pixmap is None:
            return super().sizeHint()
        else:
            w = self.width()
            return QSize(w, self.heightForWidth(w))

    def resizeEvent(self, event: QResizeEvent) -> None:
        if self._pixmap is not None:
            super().setPixmap(self.scaled_pixmap())

    def setImage(self, img):
        self.image = data_conversion.ndarray_to_qimage(img)

        self.setPixmap(QPixmap.fromImage(self.image))

    def setText(self, string: str) -> None:
        if self.text_format is None:
            self.text_format = string

        super().setText(string)

    def updateText(self, **kwargs: Any) -> None:
        if self.text_format is None:
            self.text_format = self.text()

        self.setText(self.formatter.format(self.text_format, **kwargs))

    def scaled_pixmap(self) -> QPixmap:
        return self._pixmap.scaled(self.size(),
                                   Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.FastTransformation)


class KDateTimeEdit(QDateTimeEdit):
    _overrideSteps = (
        QDateTimeEdit.Section.MonthSection,
        QDateTimeEdit.Section.DaySection,
        QDateTimeEdit.Section.HourSection,
        QDateTimeEdit.Section.MinuteSection,
        QDateTimeEdit.Section.SecondSection,
    )

    def stepEnabled(self) -> QAbstractSpinBox.StepEnabledFlag:
        if self.currentSection() in self._overrideSteps:
            step = self.StepEnabledFlag.StepNone

            if self.dateTime() < self.maximumDateTime():
                step |= self.StepEnabledFlag.StepUpEnabled

            if self.dateTime() > self.minimumDateTime():
                step |= self.StepEnabledFlag.StepDownEnabled

            return step

        return super().stepEnabled()

    def stepBy(self, steps: int) -> None:
        section = self.currentSection()

        if section not in self._overrideSteps:
            super().stepBy(steps)
            return

        dt = self.dateTime()
        section = self.currentSection()

        if section == self.Section.MonthSection:
            dt = dt.addMonths(steps)
        elif section == self.Section.DaySection:
            dt = dt.addDays(steps)
        elif section == self.Section.HourSection:
            dt = dt.addSecs(3600 * steps)
        elif section == self.Section.MinuteSection:
            dt = dt.addSecs(60 * steps)
        elif section == self.Section.SecondSection:
            dt = dt.addSecs(steps)

        self.setDateTime(dt)


class KNaNDoubleSpinbox(QDoubleSpinBox):
    _value = 0
    nanstr = '--'

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def value(self) -> float:
        if np.isnan(self._value):
            return self._value
        else:
            return super().value()

    def setValue(self, value: float) -> None:
        self._value = value
        super().setValue(value)

    def textFromValue(self, value: float) -> str:
        if np.isnan(self._value):
            return self.nanstr
        else:
            return super().textFromValue(value)

    def valueFromText(self, text: str) -> float:
        if text == self.nanstr:
            return np.nan
        else:
            return super().valueFromText(text)


class KScaledDoubleSpinbox(KNaNDoubleSpinbox):
    scale = 1

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def value(self) -> float:
        return super().value() / self.scale

    def setValue(self, d: float) -> None:
        return super().setValue(d * self.scale)

    def minimum(self) -> float:
        return super().minimum() / self.scale

    def setMinimum(self, d: float) -> None:
        return super().setMinimum(d * self.scale)

    def maximum(self) -> float:
        return super().maximum() / self.scale

    def setMaximum(self, d: float) -> None:
        return super().setMaximum(d * self.scale)

    def setScale(self, scale: float, precision: int) -> None:
        with QSignalBlocker(self):
            super().setMinimum(super().minimum() / self.scale * scale)
            super().setMaximum(super().maximum() / self.scale * scale)
            super().setValue(super().value() / self.scale * scale)
            super().setDecimals(precision)
        self.scale = scale


class KMainWindow(QMainWindow):
    windows_list = []

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.setWindowIcon(QIcon(':/assets/logo/KalAO_icon.ico'))

        KMainWindow.windows_list.append(self)

    def info_to_statusbar(self, string: str) -> None:
        if string:
            self.statusBar().showMessage(string)
        else:
            self.statusBar().clearMessage()

    def center(self) -> None:
        self.move(self.screen().geometry().center() - self.rect().center())

    def closeEvent(self, event: QCloseEvent) -> None:
        if self in KMainWindow.windows_list:
            KMainWindow.windows_list.remove(self)

        return super().closeEvent(event)


class KWidget(QWidget):
    opened = 0

    def __init__(self, *args: Any, parent: QWidget = None,
                 **kwargs: Any) -> None:
        super().__init__(parent)

        self.setWindowIcon(QIcon(':/assets/logo/KalAO_icon.ico'))
        self.resize(600, 400)
        self.move(50 + 50 * KWidget.opened, 50 + 30 * KWidget.opened)

        KWidget.opened += 1


class KHoverableGraphicsScene(QGraphicsScene):
    x: float = np.nan
    y: float = np.nan

    hovered = Signal(float, float)
    clicked = Signal(float, float)
    scrolled = Signal(float, float, int)
    dragged = Signal(float, float, float, float)

    dragging: bool = False

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.changed.connect(self.scene_updated)

    def event(self, event: QEvent) -> bool:
        if event.type() == QEvent.Type.GraphicsSceneMouseMove:
            self.x = event.scenePos().x()
            self.y = event.scenePos().y()

            self.hovered.emit(self.x, self.y)

            if self.dragging:
                if (self.x - self.prev_x)**2 + (self.y - self.prev_y)**2 >= 1:
                    self.dragged.emit(self.x, self.y, self.x - self.prev_x,
                                      self.y - self.prev_y)
                    self.prev_x = self.x
                    self.prev_y = self.y

            return True

        elif event.type() == QEvent.Type.GraphicsSceneLeave:
            self.x = np.nan
            self.y = np.nan

            self.hovered.emit(self.x, self.y)

            return True

        elif event.type() == QEvent.Type.GraphicsSceneHoverEnter:
            return True

        elif event.type() == QEvent.Type.GraphicsSceneWheel:
            x = event.scenePos().x()
            y = event.scenePos().y()

            if event.orientation() != Qt.Orientation.Vertical:
                return True

            if event.delta() > 0:
                self.scrolled.emit(x, y, 1)
            elif event.delta() < 0:
                self.scrolled.emit(x, y, -1)

            return True

        elif event.type() == QEvent.Type.GraphicsSceneMousePress:
            x = event.scenePos().x()
            y = event.scenePos().y()

            self.dragging = True

            self.prev_x = x
            self.prev_y = y

            self.clicked.emit(x, y)

            return True

        elif event.type() == QEvent.Type.GraphicsSceneMouseRelease:
            self.dragging = False

            return True

        else:
            return super().event(event)

    def scene_updated(self) -> None:
        if not (np.isnan(self.x) or np.isnan(self.y)):
            self.hovered.emit(self.x, self.y)


class KImageViewer(QGraphicsView):
    img: np.ndarray = None
    image: QImage = None
    pixmap: QPixmap = None
    pixmap_item: QGraphicsPixmapItem = None
    view: QRect = None
    margins: QMargins = QMargins(0, 0, 0, 0)
    shape: tuple[int, ...] = (0, 0)
    offset: QPointF = QPointF(0, 0)

    colormap: Colormap = colormaps.BlackBody()

    tick_visible = False
    tick_spacing = None
    tick_length = None
    tick_text_spacing = None
    tick_fontsize = None
    tick_ticks_x = None
    tick_ticks_y = None

    neindicator_visible = False
    neindicator_parallactic_angle = None

    formatter = KalAOFormatter()

    hovered = Signal(float, float, float)
    hovered_str = Signal(str)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self._scene = KHoverableGraphicsScene()
        self.setScene(self._scene)

        if config.GUI.opengl_graphicsview:
            gl = QOpenGLWidget()
            format = QSurfaceFormat()
            format.setSamples(4)
            gl.setFormat(format)
            self.setViewport(gl)

        self.setRenderHints(QPainter.RenderHint.Antialiasing |
                            QPainter.RenderHint.SmoothPixmapTransform)

        self.setStyleSheet('background: transparent')
        self.setBackgroundBrush(QBrush(Color.TRANSPARENT))

        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.neindicator_group = self._scene.createItemGroup([])
        self.axes_group = self._scene.createItemGroup([])

        # policy = self.sizePolicy()
        # policy.setVerticalPolicy(QSizePolicy.Policy.Preferred)
        # policy.setHorizontalPolicy(QSizePolicy.Policy.Preferred)
        # # policy = QSizePolicy()
        # policy.setHeightForWidth(True)
        # self.setSizePolicy(policy)

    def set_data_md(self, unit, precision, scaling=1):
        self.data_unit = unit
        self.data_precision = precision
        self.data_scaling = scaling

    def set_axis_md(self, unit, precision, scaling=1, x_offset=0, y_offset=0):
        self.axis_unit = unit
        self.axis_precision = precision
        self.axis_scaling = scaling
        self.axis_x_offset = x_offset
        self.axis_y_offset = y_offset

        self._draw_axes()

    # def hasHeightForWidth(self):
    #     return True

    def heightForWidth(self, width: int) -> int:
        if self.pixmap is None:
            return super().heightForWidth(width)
        else:
            if self.pixmap.width() == 0:
                return 0
            else:
                return round(self.pixmap.height() * width /
                             self.pixmap.width())

    def sizeHint(self) -> QSize:
        if self.pixmap is None:
            return super().sizeHint()
        else:
            w = self.width()
            return QSize(w, self.heightForWidth(w))

    def fitInView(self, rect: QRectF,
                  aspectRadioMode: Qt.AspectRatioMode = None) -> None:
        viewRect = self.viewport().rect().adjusted(self.margins.left(),
                                                   self.margins.top(),
                                                   -self.margins.right(),
                                                   -self.margins.bottom())

        xratio = viewRect.width() / rect.width()
        yratio = viewRect.height() / rect.height()

        self.scaling = xratio = yratio = min(xratio, yratio)

        self._scene.setSceneRect(
            self.view.adjusted(math.floor(-self.margins.left() / self.scaling),
                               math.floor(-self.margins.top() / self.scaling),
                               math.ceil(self.margins.right() / self.scaling),
                               math.ceil(self.margins.bottom() /
                                         self.scaling)))

        self.setTransform(QTransform(xratio, 0, 0, yratio, 0, 0))
        self.centerOn(rect.center())

        self._draw_axes()
        self._draw_neindicator()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)

        if self.view is not None:
            self.fitInView(QRectF(self.view),
                           Qt.AspectRatioMode.KeepAspectRatio)

    def setImage(self, img: np.ndarray, img_min: float | None = None,
                 img_max: float | None = None,
                 scale: Type[AbstractScale] = LinearScale, view: QRect = None,
                 offset: QPointF = None) -> None:
        if img is not None and len(img.shape) < 2:
            img = img[np.newaxis, :]

        self.img = img
        self.img_min = img_min
        self.img_max = img_max
        self.scale = scale

        if img is None:
            if self.pixmap_item is not None:
                self.pixmap_item.setPixmap(QPixmap())
            return

        self.image = data_conversion.ndarray_to_qimage(img, img_min, img_max,
                                                       self.colormap, scale)

        self.pixmap = QPixmap.fromImage(self.image)

        if self.pixmap_item is None:
            self.pixmap_item = self._scene.addPixmap(self.pixmap)
            self.pixmap_item.setAcceptHoverEvents(True)
            self._scene.hovered.connect(self.hover_to_xyv)
        else:
            self.pixmap_item.setPixmap(self.pixmap)

        if offset is None:
            self.offset = QPointF(0, 0)
        else:
            self.offset = offset

        self.pixmap_item.setOffset(self.offset)

        if view is None:
            view = self.pixmap.rect()

        if self.view != view:
            self.view = view
            self.fitInView(QRectF(self.view),
                           Qt.AspectRatioMode.KeepAspectRatio)
            self.shape = img.shape

    def updateColormap(self, colormap: Colormap) -> None:
        self.colormap = colormap

        if self.image is not None:
            self.setImage(self.img, self.img_min, self.img_max, self.scale,
                          self.view, self.offset)

    def updateScale(self, scale: Type[AbstractScale]) -> None:
        self.scale = scale

        if self.image is not None:
            self.setImage(self.img, self.img_min, self.img_max, self.scale,
                          self.view, self.offset)

    def updateMinMax(self, img_min: float, img_max: float) -> None:
        self.img_min = img_min
        self.img_max = img_max

        if self.image is not None:
            self.setImage(self.img, self.img_min, self.img_max, self.scale,
                          self.view, self.offset)

    def setView(self, shape: tuple[int, ...]) -> None:
        self.view = QRect(0, 0, shape[1], shape[0])
        self.fitInView(QRectF(self.view), Qt.AspectRatioMode.KeepAspectRatio)

    def setMargins(self, margins: QMargins) -> None:
        self.margins = margins

        if self.view is not None:
            self.fitInView(QRectF(self.view),
                           Qt.AspectRatioMode.KeepAspectRatio)

    def hover_to_xyv(self, x: float, y: float) -> None:
        if self.img is None:
            return

        if not (np.isnan(x) or np.isnan(y)):
            x_img = math.floor(x - self.offset.x())
            y_img = math.floor(y - self.offset.y())

            if 0 <= y_img < self.img.shape[0] and 0 <= x_img < self.img.shape[
                    1]:
                self.setCursor(Qt.CursorShape.CrossCursor)

                if isinstance(self.img, np.ma.masked_array):
                    v = self.img.filled()[y_img, x_img]
                else:
                    v = self.img[y_img, x_img]

                self.hovered.emit(x, y, v)
                self.hovered_str.emit(self.xyv_to_str(x, y, v))
            else:
                self.unsetCursor()
                self.hovered.emit(np.nan, np.nan, np.nan)
                self.hovered_str.emit('')
        else:
            self.unsetCursor()
            self.hovered.emit(np.nan, np.nan, np.nan)
            self.hovered_str.emit('')

    def xyv_to_str(self, x, y, v):
        x = int(x)
        y = int(y)

        return self.formatter.format(
            'X: {x:.{axis_precision}f}{axis_unit}, Y: {y:.{axis_precision}f}{axis_unit}, V: {v:.{data_precision}f}{data_unit}',
            x=(x - self.axis_x_offset) * self.axis_scaling,
            y=(y - self.axis_y_offset) * self.axis_scaling,
            v=v * self.data_scaling, axis_precision=self.axis_precision,
            axis_unit=self.axis_unit, data_precision=self.data_precision,
            data_unit=self.data_unit)

    def setTickParams(self, spacing: float, length: float, text_spacing: float,
                      fontsize: int, ticks_x: list[float],
                      ticks_y: list[float]) -> None:
        self.tick_spacing = spacing
        self.tick_length = length
        self.tick_text_spacing = text_spacing
        self.tick_fontsize = fontsize
        self.tick_ticks_x = ticks_x
        self.tick_ticks_y = ticks_y
        self.tick_visible = True

        self._draw_axes()

    def _draw_axes(self) -> None:
        if not self.tick_visible:
            return

        for item in self.axes_group.childItems():
            self._scene.removeItem(item)
            self.axes_group.removeFromGroup(item)

        width = self.view.width()
        height = self.view.height()

        spacing = self.tick_spacing / self.scaling
        length = self.tick_length / self.scaling
        text_spacing = self.tick_text_spacing / self.scaling

        pen = QPen(Color.BLACK, 0.5, Qt.PenStyle.SolidLine,
                   Qt.PenCapStyle.SquareCap, Qt.PenJoinStyle.MiterJoin)
        pen.setCosmetic(True)

        self._draw_vertical_axis(0, height, -(spacing), -(spacing + length),
                                 pen, self.tick_ticks_y)
        self._draw_vertical_axis(0, height, width + spacing, width + spacing +
                                 length, pen, self.tick_ticks_y)

        self._draw_horizontal_axis(0, width, -(spacing), -(spacing + length),
                                   pen, self.tick_ticks_x)
        self._draw_horizontal_axis(0, width, height + spacing, height +
                                   spacing + length, pen, self.tick_ticks_x)

        font = QFont()
        font.setPixelSize(self.tick_fontsize)

        self._draw_vertical_tick_labels(
            width + spacing + length + text_spacing, font, self.tick_ticks_y)
        self._draw_horizontal_tick_labels(
            height + spacing + length + text_spacing, font, self.tick_ticks_x)

        self.axes_group.setZValue(1)

    def _draw_vertical_axis(self, start: float, end: float, tick_start: float,
                            tick_end: float, pen: QPen,
                            ticks_y: list[float]) -> None:
        line = KNoAALine(tick_start, start, tick_start, end)
        line.setPen(pen)
        self._scene.addItem(line)
        self.axes_group.addToGroup(line)

        line = KNoAALine(tick_start, start, tick_end, start)
        line.setPen(pen)
        self._scene.addItem(line)
        self.axes_group.addToGroup(line)

        line = KNoAALine(tick_start, end, tick_end, end)
        line.setPen(pen)
        self._scene.addItem(line)
        self.axes_group.addToGroup(line)

        for y in ticks_y:
            line = KNoAALine(tick_start, y, tick_end, y)
            line.setPen(pen)
            self._scene.addItem(line)
            self.axes_group.addToGroup(line)

    def _draw_horizontal_axis(self, start: float, end: float,
                              tick_start: float, tick_end: float, pen: QPen,
                              ticks_x: list[float]) -> None:
        line = KNoAALine(start, tick_start, end, tick_start)
        line.setPen(pen)
        self._scene.addItem(line)
        self.axes_group.addToGroup(line)

        line = KNoAALine(start, tick_start, start, tick_end)
        line.setPen(pen)
        self._scene.addItem(line)
        self.axes_group.addToGroup(line)

        line = KNoAALine(end, tick_start, end, tick_end)
        line.setPen(pen)
        self._scene.addItem(line)
        self.axes_group.addToGroup(line)

        for x in ticks_x:
            line = KNoAALine(x, tick_start, x, tick_end)
            line.setPen(pen)
            self._scene.addItem(line)
            self.axes_group.addToGroup(line)

    def _draw_vertical_tick_labels(self, text_start: float, font: QFont,
                                   ticks_y: list[float]) -> None:
        for y in ticks_y:
            label = f'{(y - self.axis_y_offset) * self.axis_scaling:.{self.axis_precision}f}'

            text_item = OffsetedTextItem(label)
            text_item.setFont(font)
            text_item.setPos(text_start, y)
            text_item.setFlag(
                QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)
            self._scene.addItem(text_item)

            if not label.startswith('-'):
                label = '-' + label

            probe = OffsetedTextItem(label)
            probe.setFont(font)
            probe.setFlag(
                QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)

            self._scene.addItem(probe)
            text_item.setOffset(
                probe.boundingRect().width() -
                text_item.boundingRect().width(),
                -text_item.boundingRect().height() / 2)
            self._scene.removeItem(probe)

            self.axes_group.addToGroup(text_item)

    def _draw_horizontal_tick_labels(self, text_start: float, font: QFont,
                                     ticks_x: list[float]) -> None:
        for x in ticks_x:
            label = f'{(x - self.axis_x_offset) * self.axis_scaling:.{self.axis_precision}f}'

            text_item = OffsetedTextItem(label)
            text_item.setFont(font)
            text_item.setPos(x, text_start)
            text_item.setFlag(
                QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)
            self._scene.addItem(text_item)

            label = label.removeprefix('-')

            probe = OffsetedTextItem(label)
            probe.setFont(font)
            probe.setFlag(
                QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)

            self._scene.addItem(probe)
            text_item.setOffset(
                probe.boundingRect().width() / 2 -
                text_item.boundingRect().width(), 0)
            self._scene.removeItem(probe)

            self.axes_group.addToGroup(text_item)

    def setNEIndicator(self, parallactic_angle: float) -> None:
        self.neindicator_visible = True
        self.neindicator_parallactic_angle = parallactic_angle

        self._draw_neindicator()

    def _draw_neindicator(self) -> None:
        if not self.neindicator_visible:
            return

        for item in self.neindicator_group.childItems():
            self._scene.removeItem(item)
            self.neindicator_group.removeFromGroup(item)

        # Reset group position to avoid drifting
        self.neindicator_group.setPos(0, 0)

        pen = QPen(Color.PURPLE, 2, Qt.PenStyle.SolidLine,
                   Qt.PenCapStyle.SquareCap, Qt.PenJoinStyle.MiterJoin)
        pen.setCosmetic(True)

        brush = QBrush(Color.PURPLE, Qt.BrushStyle.SolidPattern)

        font = QFont()
        font.setPixelSize(20)
        font.setBold(True)

        angle = self.neindicator_parallactic_angle * np.pi / 180
        length = 45 / self.scaling
        arrow_size = 15 / self.scaling
        margin = 10 / self.scaling

        center_point = QPointF(0, 0)

        north_point = center_point + QPointF(
            np.cos(angle) * length,
            np.sin(angle) * length)
        north_line = QLineF(center_point, north_point)

        east_point = center_point + QPointF(-np.sin(angle) * length,
                                            -np.cos(angle) * length)
        east_line = QLineF(center_point, east_point)

        north_arrow_p0 = north_point + QPointF(
            north_line.unitVector().dx() * arrow_size / 2,
            north_line.unitVector().dy() * arrow_size / 2)
        north_arrow_p1 = north_arrow_p0 + QPointF(
            -np.sin(angle + np.pi / 3) * arrow_size,
            -np.cos(angle + np.pi / 3) * arrow_size)
        north_arrow_p2 = north_arrow_p0 + QPointF(
            -np.sin(angle + 2 * np.pi / 3) * arrow_size,
            -np.cos(angle + 2 * np.pi / 3) * arrow_size)

        east_arrow_p0 = east_point + QPointF(
            east_line.unitVector().dx() * arrow_size / 2,
            east_line.unitVector().dy() * arrow_size / 2)
        east_arrow_p1 = east_arrow_p0 + QPointF(
            np.cos(angle + np.pi / 3) * arrow_size,
            np.sin(angle + np.pi / 3) * arrow_size)
        east_arrow_p2 = east_arrow_p0 + QPointF(
            np.cos(angle + 2 * np.pi / 3) * arrow_size,
            np.sin(angle + 2 * np.pi / 3) * arrow_size)

        north_east_path = QPainterPath(north_point)
        north_east_path.lineTo(center_point)
        north_east_path.lineTo(east_point)

        north_east = self._scene.addPath(north_east_path, pen)

        pen = QPen(Color.TRANSPARENT, 0, Qt.PenStyle.SolidLine,
                   Qt.PenCapStyle.SquareCap, Qt.PenJoinStyle.MiterJoin)
        pen.setCosmetic(True)

        north_arrow = self._scene.addPolygon(
            QPolygonF([north_arrow_p0, north_arrow_p1, north_arrow_p2]), pen,
            brush)
        east_arrow = self._scene.addPolygon(
            QPolygonF([east_arrow_p0, east_arrow_p1, east_arrow_p2]), pen,
            brush)

        north_textitem = CenteredTextItem('N')
        north_textitem.setFont(font)
        north_textitem.setPos(north_point +
                              QPointF(north_line.unitVector().dx(),
                                      north_line.unitVector().dy()) * 1.5 *
                              arrow_size)
        north_textitem.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)
        north_textitem.setBrush(brush)
        self._scene.addItem(north_textitem)

        east_textitem = CenteredTextItem('E')
        east_textitem.setFont(font)
        east_textitem.setPos(east_point +
                             QPointF(east_line.unitVector().dx(),
                                     east_line.unitVector().dy()) * 1.5 *
                             arrow_size)
        east_textitem.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)
        east_textitem.setBrush(brush)
        self._scene.addItem(east_textitem)

        self.neindicator_group.addToGroup(north_east)
        self.neindicator_group.addToGroup(north_arrow)
        self.neindicator_group.addToGroup(east_arrow)
        self.neindicator_group.addToGroup(north_textitem)
        self.neindicator_group.addToGroup(east_textitem)
        self.neindicator_group.setZValue(1)

        rect = self.neindicator_group.childrenBoundingRect()
        self.neindicator_group.setPos(-rect.x() + margin, -rect.y() + margin)


class KChart(QChart):
    hovered = Signal(QAbstractSeries, float, float)

    point_size = 2
    current_hovered_index = None

    pos = None

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def addAxis(self, axis: QAbstractAxis, alignment: Qt.AlignmentFlag):
        super().addAxis(axis, alignment)

        if hasattr(axis, 'rangeChanged'):
            axis.rangeChanged.connect(self.rangeChanged)

    def rangeChanged(self, min: float, max: float) -> None:
        if self.current_hovered_index is not None:
            return

        if self.pos is None:
            return

        pos_values = self.mapToValue(self.mapFromParent(self.pos))
        self.hovered.emit(None, pos_values.x(), pos_values.y())

    def mouseEvent(self, event: QMouseEvent) -> None:
        if self.current_hovered_index is not None:
            return

        if event.type() == QEvent.Type.Leave:
            self.pos = None
            self.hovered.emit(None, np.nan, np.nan)
        else:
            self.pos = event.pos()

            if self.plotArea().contains(self.pos):
                pos_values = self.mapToValue(self.mapFromParent(self.pos))
                self.hovered.emit(None, pos_values.x(), pos_values.y())
            else:
                self.pos = None
                self.hovered.emit(None, np.nan, np.nan)

    def pointHoveredEvent(self, point: QPointF, state: bool,
                          series: QXYSeries) -> None:
        points = series.points()

        closest_point, closest_index = self.find_closest_point(point, points)
        if self.current_hovered_index is not None:
            if series.pointsVisible():
                series.setPointConfiguration(self.current_hovered_index, {
                    QXYSeries.PointConfiguration.Size: self.point_size
                })
            self.hovered.emit(series, np.nan, np.nan)
            self.current_hovered_index = None

        if not self.point_visible(series, closest_index):
            return

        if state:
            if series.pointsVisible():
                series.setPointConfiguration(closest_index, {
                    QXYSeries.PointConfiguration.Size: 2 * self.point_size
                })

            self.hovered.emit(series, closest_point.x(), closest_point.y())
            self.current_hovered_index = closest_index
        else:
            if series.pointsVisible():
                series.setPointConfiguration(closest_index, {
                    QXYSeries.PointConfiguration.Size: self.point_size
                })

            self.hovered.emit(series, np.nan, np.nan)
            self.current_hovered_index = None

    def point_visible(self, series: QXYSeries, index: int) -> bool:
        for k, v in series.pointConfiguration(index).items():
            if k == QXYSeries.PointConfiguration.Visibility:
                return v

        return True

    def find_closest_point(self, point: QPointF, points: list[QPointF]):
        closest_point = min(points,
                            key=lambda p: self.points_distance(p, point))
        closest_index = points.index(closest_point)

        return closest_point, closest_index

    def points_distance(self, point1: QPointF, point2: QPointF) -> float:
        diff = point2 - point1

        axis_x = self.axisX()

        if isinstance(axis_x, QDateTimeAxis):
            x_max = axis_x.max().toMSecsSinceEpoch()
            x_min = axis_x.min().toMSecsSinceEpoch()
        else:
            x_max = axis_x.max()
            x_min = axis_x.min()

        x = diff.x() / (x_max-x_min)
        y = diff.y() / (self.axisY().max() - self.axisY().min())

        return x**2 + y**2


class KChartView(QChartView):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.setRenderHint(QPainter.RenderHint.Antialiasing)

        chart = KChart()
        chart.setMargins(QMargins(0, 0, 0, 0))
        chart.setBackgroundVisible(True)

        self.setStyleSheet('background: transparent')

        self.setChart(chart)

        self._value_pos = QPoint()
        self.setMouseTracking(True)

        self.vlines = []
        self.hlines = []

    def updateMinMax(self, y_min: float, y_max: float) -> None:
        self.chart().axisY().setRange(y_min, y_max)

    def drawForeground(self, painter: QPainter, rect: QRectF) -> None:
        super().drawForeground(painter, rect)

        painter.save()

        area = self.chart().plotArea()

        for x, color in self.vlines:
            pen = QPen(color, 0.5, Qt.PenStyle.DashLine,
                       Qt.PenCapStyle.FlatCap, Qt.PenJoinStyle.MiterJoin)
            painter.setPen(pen)

            pos = self.chart().mapToPosition(QPoint(x, 0))

            y1 = QPointF(pos.x(), area.top() + pen.width() / 2)
            y2 = QPointF(pos.x(), area.bottom() - pen.width() / 2)

            if area.left() <= pos.x() <= area.right():
                painter.drawLine(y1, y2)

        for y, color in self.hlines:
            pen = QPen(color, 1, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap,
                       Qt.PenJoinStyle.MiterJoin)
            painter.setPen(pen)

            pos = self.chart().mapToPosition(QPointF(0, y))

            x1 = QPointF(area.left() + pen.width() / 2, pos.y())
            x2 = QPointF(area.right() - pen.width() / 2, pos.y())

            if area.left() <= pos.y() <= area.right():
                painter.drawLine(x1, x2)

        if not self._value_pos.isNull():
            pen = QPen(Color.GREY, 0.5, Qt.PenStyle.DashLine,
                       Qt.PenCapStyle.FlatCap, Qt.PenJoinStyle.MiterJoin)
            painter.setPen(pen)

            sp = self._value_pos
            x1 = QPointF(area.left() + pen.width() / 2, sp.y())
            x2 = QPointF(area.right() - pen.width() / 2, sp.y())
            y1 = QPointF(sp.x(), area.top() + pen.width() / 2)
            y2 = QPointF(sp.x(), area.bottom() - pen.width() / 2)

            if area.left() <= sp.x() <= area.right():
                painter.drawLine(y1, y2)
            if area.top() <= sp.y() <= area.bottom():
                painter.drawLine(x1, x2)

        painter.restore()

    def resetVLines(self) -> None:
        self.vlines = []

    def resetHLines(self) -> None:
        self.hlines = []

    def addVLine(self, x: float, color: QColor) -> None:
        self.vlines.append((x, color))

    def addHLine(self, y: float, color: QColor) -> None:
        self.hlines.append((y, color))

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        super().mouseMoveEvent(event)

        if self.chart() is None:
            return

        self.chart().mouseEvent(event)

        pos = self.mapToScene(event.pos())

        if self.chart().plotArea().contains(pos):
            self._value_pos = pos
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self._value_pos = QPoint()
            self.unsetCursor()

        self.update()

    def event(self, event: QEvent) -> bool:
        if self.chart() is None:
            return super().event(event)

        if event.type() == QEvent.Type.Leave:
            self._value_pos = QPoint()
            self.unsetCursor()

            self.chart().mouseEvent(event)

        return super().event(event)


class KDraggableChartView(KChartView):
    drag_max: float = 1
    drag_min: float = 0

    dragged = Signal(QAbstractSeries, float, float)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        chart = self.chart()

        chart.current_dragged_series = None
        chart.current_dragged_point = None
        chart.current_dragged_index = None

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        chart = self.chart()

        if chart.current_dragged_index is not None:
            pos = chart.mapToValue(event.pos(), chart.current_dragged_series)

            x = chart.current_dragged_point.x()
            y = max(min(pos.y(), self.drag_max), self.drag_min)

            chart.current_dragged_series.replace(chart.current_dragged_index,
                                                 QPointF(x, y))

            self.dragged.emit(chart.current_dragged_series, x, y)

        super().mouseMoveEvent(event)


class KMessageBox(QMessageBox):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def show(self) -> None:
        super().show()

        font_matrix = self.fontMetrics()
        width = font_matrix.boundingRect(self.informativeText()).width()

        spacer = QSpacerItem(width, 0, QSizePolicy.Policy.Minimum,
                             QSizePolicy.Policy.Expanding)
        self.layout().addItem(spacer,
                              self.layout().rowCount(), 0, 1,
                              self.layout().columnCount())


class KStatusIndicator(QGraphicsView):
    diameter: float = 128
    border: float = 16
    view = QRectF(-border / 2, -border / 2, diameter + border,
                  diameter + border)

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        self._scene = QGraphicsScene()
        self.setScene(self._scene)

        self.setRenderHints(QPainter.RenderHint.Antialiasing |
                            QPainter.RenderHint.SmoothPixmapTransform)

        self.setStyleSheet('background: transparent')

        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.pen = QPen(Color.GREY, self.border, Qt.PenStyle.SolidLine,
                        Qt.PenCapStyle.SquareCap, Qt.PenJoinStyle.MiterJoin)
        self.brush = QBrush(Color.GREY.lighter(175),
                            Qt.BrushStyle.SolidPattern)

        self.ellipse = self._scene.addEllipse(0, 0, self.diameter,
                                              self.diameter, self.pen,
                                              self.brush)

        self.fitInView(self.view, Qt.AspectRatioMode.KeepAspectRatio)

    def setStatus(self, color: QColor = Color.DARK_GREY,
                  tooltip: str = '') -> None:
        if color == Color.BLACK:
            color = QColor('#333333')

        self.brush.setColor(color)
        self.ellipse.setBrush(self.brush)
        self.pen.setColor(color.lighter(175))
        self.ellipse.setPen(self.pen)
        self.setToolTip(f'Status: {tooltip}')

    def heightForWidth(self, width: int) -> int:
        return width

    def sizeHint(self) -> QSize:
        w = self.width()
        return QSize(w, self.heightForWidth(w))

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)

        self.fitInView(self.view, Qt.AspectRatioMode.KeepAspectRatio)


class KColorbar(QGraphicsView):
    view: QRect = None
    margins: QMargins = QMargins(0, 0, 0, 0)

    scale: Type[AbstractScale] = LinearScale
    img_min: float = np.nan
    img_max: float = np.nan
    true_min: float = np.nan
    true_max: float = np.nan

    nb_ticks: int = 7
    margin: int = 75
    tick_length: float = 5
    tick_text_spacing: float = 5

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        self._scene = QGraphicsScene()
        self.setScene(self._scene)

        self.setRenderHints(QPainter.RenderHint.Antialiasing |
                            QPainter.RenderHint.SmoothPixmapTransform)

        self.setStyleSheet('background: transparent')
        self.setBackgroundBrush(QBrush(Color.TRANSPARENT))

        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.ticks_group = self._scene.createItemGroup([])
        self.pixmap_item = self._scene.addPixmap(QPixmap())

        pen = QPen(Color.BLACK, 0.5, Qt.PenStyle.SolidLine,
                   Qt.PenCapStyle.FlatCap, Qt.PenJoinStyle.MiterJoin)
        pen.setCosmetic(True)

        self.border = KNoAARect(0, 0, 1, 1)
        self.border.setPen(pen)
        self._scene.addItem(self.border)
        self.border.setZValue(1)

    def draw_colorbar(self) -> None:
        colorbar_width = self.size().width() - self.margin

        scale = self.scale(0, 255)

        if self.img_min < self.true_min:
            i_min = 0
            colorbar_min = self.true_min
        else:
            i_min = scale.scale((self.img_min - self.true_min) /
                                (self.true_max - self.true_min) * 255)
            colorbar_min = self.img_min

        if self.img_max > self.true_max:
            i_max = 255
            colorbar_max = self.true_max
        else:
            i_max = scale.scale((self.img_max - self.true_min) /
                                (self.true_max - self.true_min) * 255)
            colorbar_max = self.img_max

        colorbar_min = data_conversion.ndarray_normalize(
            colorbar_min, self.img_min, self.img_max, colormap=self.colormap,
            scale=self.scale)

        colorbar_max = data_conversion.ndarray_normalize(
            colorbar_max, self.img_min, self.img_max, colormap=self.colormap,
            scale=self.scale)

        pixels = []
        for i in np.linspace(0, 255, 256):
            if i < i_min:
                pixels.append(colorbar_min)
            elif i > i_max:
                pixels.append(colorbar_max)
            else:
                pixels.append((i-i_min) / (i_max-i_min) *
                              (colorbar_max-colorbar_min) + colorbar_min)

        pixels = np.flip(np.rint(np.array(pixels))[:, np.newaxis])

        img_uint8 = np.require(pixels, np.uint8, 'C')
        image = QImage(img_uint8.data, img_uint8.shape[1], img_uint8.shape[0],
                       img_uint8.shape[1], QImage.Format.Format_Indexed8)
        image.setColorTable(self.colormap.table)

        self.pixmap = QPixmap.fromImage(image).scaled(colorbar_width, 256)
        self.pixmap_item.setPixmap(self.pixmap)

        self.view = self.pixmap.rect().adjusted(
            -self.margins.left(), -self.margins.top(), self.margins.right(),
            self.margins.bottom()).adjusted(0, -5, self.margin, 5)

        self.fitInView(self.view, Qt.AspectRatioMode.IgnoreAspectRatio)

        self.border.setRect(self.pixmap_item.pixmap().rect())

        for item in self.ticks_group.childItems():
            self._scene.removeItem(item)
            self.ticks_group.removeFromGroup(item)

        pen = QPen(Color.BLACK, 0.5, Qt.PenStyle.SolidLine,
                   Qt.PenCapStyle.FlatCap, Qt.PenJoinStyle.MiterJoin)
        pen.setCosmetic(True)

        font = QFont()
        font.setPixelSize(10)

        for i in np.linspace(0, 255, self.nb_ticks):
            line = KNoAALine(colorbar_width, 255.5 - i,
                             colorbar_width + self.tick_length, 255.5 - i)
            line.setPen(pen)
            self._scene.addItem(line)
            self.ticks_group.addToGroup(line)

            v = scale.inverse(i) / 255 * (self.true_max -
                                          self.true_min) + self.true_min

            text_item = OffsetedTextItem(f'{v:3.3g}')
            text_item.setFont(font)
            text_item.setPos(
                colorbar_width + self.tick_length + self.tick_text_spacing,
                255.5 - i)
            text_item.setFlag(
                QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)
            self._scene.addItem(text_item)
            self.ticks_group.addToGroup(text_item)

            probe = OffsetedTextItem(f'{v:3.3g}')  # TODO minus?
            probe.setFont(font)
            probe.setFlag(
                QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)

            self._scene.addItem(probe)
            text_item.setOffset(
                0,
                probe.boundingRect().height() / 2 -
                text_item.boundingRect().height())
            self._scene.removeItem(probe)

    def setTrueMinMax(self, true_min: float, true_max: float) -> None:
        self.true_min = true_min
        self.true_max = true_max

        self.draw_colorbar()

    def setColormap(self, colormap: Colormap) -> None:
        self.colormap = colormap

        self.draw_colorbar()

    def updateMinMax(self, img_min: float, img_max: float) -> None:
        self.img_min = img_min
        self.img_max = img_max

        self.draw_colorbar()

    def updateScale(self, scale: Type[AbstractScale]) -> None:
        self.scale = scale

        self.draw_colorbar()

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)

        if self.view is not None:
            self.fitInView(self.view, Qt.AspectRatioMode.IgnoreAspectRatio)
