import math

import numpy as np

from PySide6.QtCharts import (QAbstractSeries, QChart, QChartView,
                              QDateTimeAxis, QXYSeries)
from PySide6.QtCore import (QEvent, QLineF, QMargins, QMarginsF, QPoint,
                            QPointF, QRect, QRectF, QSignalBlocker, QSize,
                            Signal)
from PySide6.QtGui import (QBrush, QFont, QGuiApplication, QIcon, QImage,
                           QPainter, QPainterPath, QPen, QPixmap, QPolygonF,
                           QSurfaceFormat, Qt, QTransform)
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (QDateTimeEdit, QDoubleSpinBox, QGraphicsItem,
                               QGraphicsScene, QGraphicsSimpleTextItem,
                               QGraphicsView, QLabel, QLineEdit,
                               QListWidgetItem, QMainWindow, QMessageBox,
                               QSizePolicy, QSpacerItem, QWidget)

from kalao.utils.image import LinearScale

from guis.utils import colormaps, data_conversion
from guis.utils.definitions import Color, Logo
from guis.utils.string_formatter import KalAOFormatter

import config


class OffsetedTextItem(QGraphicsSimpleTextItem):
    offset_x = 0
    offset_y = 0

    def setOffset(self, x, y):
        self.offset_x = x
        self.offset_y = y

    def paint(self, painter, option, widget):
        painter.translate(self.boundingRect().topLeft())
        super().paint(painter, option, widget)
        painter.translate(-self.boundingRect().topLeft())

    def boundingRect(self):
        b = super().boundingRect()
        return QRectF(b.x() + self.offset_x,
                      b.y() + self.offset_y, b.width(), b.height())


class KLabel(QLabel):
    _pixmap = None
    text_format = None
    formatter = KalAOFormatter()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if len(args) > 0 and isinstance(args[0], str):
            self.text_format = args[0]

    def setPixmap(self, p):
        self._pixmap = p
        super().setPixmap(self.scaledPixmap())

    def heightForWidth(self, width):
        if self._pixmap is None:
            super().heightForWidth(width)
        else:
            return self._pixmap.height() * width / self._pixmap.width()

    def sizeHint(self):
        if self._pixmap is None:
            return super().sizeHint()
        else:
            w = self.width()
            return QSize(w, self.heightForWidth(w))

    def scaledPixmap(self):
        return self._pixmap.scaled(self.size(), Qt.KeepAspectRatio,
                                   Qt.FastTransformation)

    def resizeEvent(self, e):
        if self._pixmap is not None:
            super().setPixmap(self.scaledPixmap())

    def setImage(self, img):
        self.image = data_conversion.ndarray_to_qimage(img)

        self.setPixmap(QPixmap.fromImage(self.image))

    def setText(self, str):
        if self.text_format is None:
            self.text_format = str

        super().setText(str)

    def updateText(self, **kwargs):
        if self.text_format is None:
            self.text_format = self.text()

        self.setText(self.formatter.format(self.text_format, **kwargs))


class KLineEdit(QLineEdit):
    text_format = None
    formatter = KalAOFormatter()

    def __init__(self, arg0=None, *args, **kwargs):
        super().__init__(arg0, *args, **kwargs)

        if isinstance(arg0, str):
            self.text_format = arg0

    def setText(self, str):
        if self.text_format is None:
            self.text_format = str

        super().setText(str)

    def updateText(self, **kwargs):
        if self.text_format is None:
            self.text_format = self.text()

        self.setText(self.formatter.format(self.text_format, **kwargs))


class KDateTimeEdit(QDateTimeEdit):
    _overrideSteps = (
        QDateTimeEdit.Section.MonthSection,
        QDateTimeEdit.Section.DaySection,
        QDateTimeEdit.Section.HourSection,
        QDateTimeEdit.Section.MinuteSection,
        QDateTimeEdit.Section.SecondSection,
    )

    def stepEnabled(self):
        if self.currentSection() in self._overrideSteps:
            step = self.StepEnabledFlag.StepNone

            if self.dateTime() < self.maximumDateTime():
                step |= self.StepEnabledFlag.StepUpEnabled

            if self.dateTime() > self.minimumDateTime():
                step |= self.StepEnabledFlag.StepDownEnabled

            return step

        return super().stepEnabled()

    def stepBy(self, steps):
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


class KScaledDoubleSpinbox(QDoubleSpinBox):
    scale = 1

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def value(self):
        return super().value() / self.scale

    def setValue(self, d):
        return super().setValue(d * self.scale)

    def minimum(self):
        return super().minimum() / self.scale

    def setMinimum(self, d):
        return super().setMinimum(d * self.scale)

    def maximum(self):
        return super().maximum() / self.scale

    def setMaximum(self, d):
        return super().setMaximum(d * self.scale)

    def setScale(self, scale, precision):
        with QSignalBlocker(self):
            super().setMinimum(super().minimum() / self.scale * scale)
            super().setMaximum(super().maximum() / self.scale * scale)
            super().setValue(super().value() / self.scale * scale)
            super().setDecimals(precision)
        self.scale = scale


class KSvgWidget(QSvgWidget):
    pass


class KMainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowIcon(QIcon(str(Logo.ico)))

    def info_to_statusbar(self, string):
        if string:
            self.statusBar().showMessage(string)
        else:
            self.statusBar().clearMessage()

    def center(self):
        self.move(
            QGuiApplication.primaryScreen().availableGeometry().center() -
            self.rect().center())


class KDetachedTabWindow(KMainWindow):
    def __init__(self, widget, *args, **kwargs):
        super().__init__(*args, **kwargs)

        parent = kwargs['parent']

        self.parent = parent

        self.setWindowTitle(widget.windowTitle())
        self.setCentralWidget(widget)
        self.resize(parent.size())
        self.show()
        self.center()

        if hasattr(widget, 'hovered'):
            self.statusBar().show()
            widget.hovered.disconnect(self.parent.info_to_statusbar)
            widget.hovered.connect(self.info_to_statusbar)

        widget.show()

    def closeEvent(self, event):
        widget = self.centralWidget()

        i = self.parent.widgets.index(widget)

        while i > 0:
            i -= 1
            j = self.parent.tabwidget.indexOf(self.parent.widgets[i])
            if j != -1:
                self.parent.tabwidget.insertTab(
                    j + 1, widget,
                    widget.windowTitle().removesuffix(" - KalAO"))
                self.parent.tabwidget.setCurrentIndex(j + 1)
                break
        else:
            self.parent.tabwidget.addTab(
                widget,
                widget.windowTitle().removesuffix(" - KalAO"))

        if hasattr(widget, 'hovered'):
            widget.hovered.disconnect(self.info_to_statusbar)
            widget.hovered.connect(self.parent.info_to_statusbar)

        event.accept()


class KWidget(QWidget):
    opened = 0

    def __init__(self, *args, parent=None, **kwargs):
        super().__init__(parent)

        self.setWindowIcon(QIcon(str(Logo.ico)))
        self.resize(600, 400)
        self.move(50 + 50 * KWidget.opened, 50 + 30 * KWidget.opened)

        KWidget.opened += 1


class KListWidgetItem(QListWidgetItem):
    def __init__(self, key, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.key = key


class KHoverableGraphicsScene(QGraphicsScene):
    x = np.nan
    y = np.nan

    hovered = Signal(float, float)
    clicked = Signal(float, float)
    scrolled = Signal(float, float, int)
    dragged = Signal(float, float, float, float)

    dragging = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.changed.connect(self.scene_updated)

    def event(self, event):
        if event.type() == QEvent.GraphicsSceneMouseMove:
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

        elif event.type() == QEvent.GraphicsSceneLeave:
            self.x = np.nan
            self.y = np.nan

            self.hovered.emit(self.x, self.y)

            return True

        elif event.type() == QEvent.GraphicsSceneHoverEnter:
            return True

        elif event.type() == QEvent.GraphicsSceneWheel:
            x = event.scenePos().x()
            y = event.scenePos().y()

            if event.pixelDelta().y() > 0:
                self.scrolled.emit(x, y, 1)
            elif event.pixelDelta().y() < 0:
                self.scrolled.emit(x, y, -1)

            return True

        elif event.type() == QEvent.GraphicsSceneMousePress:
            x = event.scenePos().x()
            y = event.scenePos().y()

            self.dragging = True

            self.prev_x = x
            self.prev_y = y

            self.clicked.emit(x, y)

            return True

        elif event.type() == QEvent.GraphicsSceneMouseRelease:
            self.dragging = False

            return True

        else:
            return super().event(event)

    def scene_updated(self):
        if not (np.isnan(self.x) or np.isnan(self.y)):
            self.hovered.emit(self.x, self.y)


class KGraphicsView(QGraphicsView):
    img = None
    image = None
    pixmap = None
    pixmap_item = None
    view = None
    margins = QMarginsF(0, 0, 0, 0)
    shape = (0, 0)
    offset = QPointF(0, 0)

    colormap = colormaps.BlackBody()

    tick_visible = False
    tick_spacing = None
    tick_length = None
    tick_text_spacing = None
    tick_fontsize = None
    tick_ticks_x = None
    tick_ticks_y = None

    neindicator_visible = False
    neindicator_parallactic_angle = None

    hovered = Signal(float, float, float)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._scene = KHoverableGraphicsScene()
        self.setScene(self._scene)

        if config.GUI.opengl_graphicsview:
            gl = QOpenGLWidget()
            format = QSurfaceFormat()
            format.setSamples(4)
            gl.setFormat(format)
            self.setViewport(gl)

        self.setRenderHints(QPainter.Antialiasing |
                            QPainter.SmoothPixmapTransform)

        self.setStyleSheet("background: transparent")
        self.setBackgroundBrush(QBrush(Color.TRANSPARENT))

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.neindicator_group = self._scene.createItemGroup([])
        self.axes_group = self._scene.createItemGroup([])

        # policy = self.sizePolicy()
        # policy.setVerticalPolicy(QSizePolicy.Preferred)
        # policy.setHorizontalPolicy(QSizePolicy.Preferred)
        # # policy = QSizePolicy()
        # policy.setHeightForWidth(True)
        # self.setSizePolicy(policy)

    # def hasHeightForWidth(self):
    #     return True

    def heightForWidth(self, width):
        if self.pixmap is None:
            return super().heightForWidth(width)
        else:
            if self.pixmap.width() == 0:
                return 0
            else:
                return self.pixmap.height() * width / self.pixmap.width()

    def sizeHint(self):
        if self.pixmap is None:
            return super().sizeHint()
        else:
            w = self.width()
            return QSize(w, self.heightForWidth(w))

    def fitInView(self, rect, aspectRadioMode=None):
        viewRect = self.viewport().rect().adjusted(self.margins.left(),
                                                   self.margins.top(),
                                                   -self.margins.right(),
                                                   -self.margins.bottom())

        xratio = viewRect.width() / rect.width()
        yratio = viewRect.height() / rect.height()

        self.scaling = xratio = yratio = min(xratio, yratio)

        self._scene.setSceneRect(
            self.view.adjusted(-self.margins.left() / self.scaling,
                               -self.margins.top() / self.scaling,
                               self.margins.right() / self.scaling,
                               self.margins.bottom() / self.scaling))

        self.setTransform(QTransform(xratio, 0, 0, yratio, 0, 0))
        self.centerOn(rect.center())

        if self.tick_visible:
            self._draw_axes()

        if self.neindicator_visible:
            self._draw_neindicator()

    def resizeEvent(self, e):
        super().resizeEvent(e)

        if self.view is not None:
            self.fitInView(self.view, Qt.KeepAspectRatio)

    def setImage(self, img, img_min=None, img_max=None, scale=LinearScale,
                 view=None, offset=None):
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
            self.fitInView(self.view, Qt.KeepAspectRatio)
            self.shape = img.shape

    def updateColormap(self, colormap):
        self.colormap = colormap

        if self.image is not None:
            self.setImage(self.img, self.img_min, self.img_max, self.scale,
                          self.view, self.offset)

    def updateScale(self, scale):
        self.scale = scale

        if self.image is not None:
            self.setImage(self.img, self.img_min, self.img_max, self.scale,
                          self.view, self.offset)

    def updateMinMax(self, img_min, img_max):
        self.img_min = img_min
        self.img_max = img_max

        if self.image is not None:
            self.setImage(self.img, self.img_min, self.img_max, self.scale,
                          self.view, self.offset)

    def setView(self, shape):
        self.view = QRect(0, 0, shape[1], shape[0])
        self.fitInView(self.view, Qt.KeepAspectRatio)

    def setMargins(self, margins):
        self.margins = margins

        if self.view is not None:
            self.fitInView(self.view, Qt.KeepAspectRatio)

    def hover_to_xyv(self, x, y):
        if self.img is None:
            return

        if not (np.isnan(x) or np.isnan(y)):
            x_img = math.floor(x - self.offset.x())
            y_img = math.floor(y - self.offset.y())

            if 0 <= y_img < self.img.shape[0] and 0 <= x_img < self.img.shape[
                    1]:
                self.setCursor(Qt.CrossCursor)
                if np.ma.is_masked(self.img):
                    self.hovered.emit(x, y, self.img.filled()[y_img, x_img])
                else:
                    self.hovered.emit(x, y, self.img[y_img, x_img])
            else:
                self.unsetCursor()
                self.hovered.emit(np.nan, np.nan, np.nan)
        else:
            self.unsetCursor()
            self.hovered.emit(np.nan, np.nan, np.nan)

    def setTickParams(self, spacing, length, text_spacing, fontsize, ticks_x,
                      ticks_y):
        self.tick_spacing = spacing
        self.tick_length = length
        self.tick_text_spacing = text_spacing
        self.tick_fontsize = fontsize
        self.tick_ticks_x = ticks_x
        self.tick_ticks_y = ticks_y
        self.tick_visible = True

        self._draw_axes()

    def _draw_axes(self):
        for item in self.axes_group.childItems():
            self._scene.removeItem(item)
            self.axes_group.removeFromGroup(item)

        width = self.view.width()
        height = self.view.height()

        spacing = self.tick_spacing / self.scaling
        length = self.tick_length / self.scaling
        text_spacing = self.tick_text_spacing / self.scaling

        pen = QPen(Color.BLACK, 0.5, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin)
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

    def _draw_vertical_axis(self, start, end, tick_start, tick_end, pen,
                            ticks_y):
        self.axes_group.addToGroup(
            self._scene.addLine(tick_start, start, tick_start, end, pen))

        self.axes_group.addToGroup(
            self._scene.addLine(tick_start, start, tick_end, start, pen))
        self.axes_group.addToGroup(
            self._scene.addLine(tick_start, end, tick_end, end, pen))

        for y, label in ticks_y:
            self.axes_group.addToGroup(
                self._scene.addLine(tick_start, y, tick_end, y, pen))

    def _draw_horizontal_axis(self, start, end, tick_start, tick_end, pen,
                              ticks_x):
        self.axes_group.addToGroup(
            self._scene.addLine(start, tick_start, end, tick_start, pen))

        self.axes_group.addToGroup(
            self._scene.addLine(start, tick_start, start, tick_end, pen))
        self.axes_group.addToGroup(
            self._scene.addLine(end, tick_start, end, tick_end, pen))

        for x, label in ticks_x:
            self.axes_group.addToGroup(
                self._scene.addLine(x, tick_start, x, tick_end, pen))

    def _draw_vertical_tick_labels(self, text_start, font, ticks_y):
        for y, label in ticks_y:
            text_item = OffsetedTextItem(label)
            text_item.setFont(font)
            text_item.setPos(text_start, y)
            text_item.setFlag(QGraphicsItem.ItemIgnoresTransformations)
            self._scene.addItem(text_item)

            if not label.startswith('-'):
                label = '-' + label

            probe = OffsetedTextItem(label)
            probe.setFont(font)
            probe.setFlag(QGraphicsItem.ItemIgnoresTransformations)

            self._scene.addItem(probe)
            text_item.setOffset(
                probe.boundingRect().width() -
                text_item.boundingRect().width(),
                -text_item.boundingRect().height() / 2)
            self._scene.removeItem(probe)

            self.axes_group.addToGroup(text_item)

    def _draw_horizontal_tick_labels(self, text_start, font, ticks_x):
        for x, label in ticks_x:
            text_item = OffsetedTextItem(label)
            text_item.setFont(font)
            text_item.setPos(x, text_start)
            text_item.setFlag(QGraphicsItem.ItemIgnoresTransformations)
            self._scene.addItem(text_item)

            label = label.removeprefix('-')

            probe = OffsetedTextItem(label)
            probe.setFont(font)
            probe.setFlag(QGraphicsItem.ItemIgnoresTransformations)

            self._scene.addItem(probe)
            text_item.setOffset(
                probe.boundingRect().width() / 2 -
                text_item.boundingRect().width(), 0)
            self._scene.removeItem(probe)

            self.axes_group.addToGroup(text_item)

    def setNEIndicator(self, parallactic_angle):
        self.neindicator_visible = True
        self.neindicator_parallactic_angle = parallactic_angle

        self._draw_neindicator()

    def _draw_neindicator(self):
        for item in self.neindicator_group.childItems():
            self._scene.removeItem(item)
            self.neindicator_group.removeFromGroup(item)

        # Reset group position to avoid drifting
        self.neindicator_group.setPos(0, 0)

        pen = QPen(Color.GREEN, 1.25, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin)
        pen.setCosmetic(True)

        brush = QBrush(Color.GREEN, Qt.SolidPattern)

        font = QFont()
        font.setPixelSize(10)
        font.setBold(True)

        angle = self.neindicator_parallactic_angle * np.pi / 180
        length = 15 / self.scaling
        arrow_size = 5 / self.scaling
        margin = 5 / self.scaling

        center_point = QPointF(0, 0)

        north_point = center_point + QPointF(-np.sin(angle) * length,
                                             -np.cos(angle) * length)
        north_line = QLineF(center_point, north_point)

        east_point = center_point + QPointF(
            np.cos(angle) * length, -np.sin(angle) * length)
        east_line = QLineF(center_point, east_point)

        north_arrow_p0 = north_point + QPointF(
            north_line.unitVector().dx(),
            north_line.unitVector().dy()) * arrow_size / 2
        north_arrow_p1 = north_arrow_p0 + QPointF(
            np.cos(-angle + np.pi / 3) * arrow_size,
            np.sin(-angle + np.pi / 3) * arrow_size)
        north_arrow_p2 = north_arrow_p0 + QPointF(
            np.cos(-angle + np.pi - np.pi / 3) * arrow_size,
            np.sin(-angle + np.pi - np.pi / 3) * arrow_size)

        east_arrow_p0 = east_point + QPointF(
            east_line.unitVector().dx(),
            east_line.unitVector().dy()) * arrow_size / 2
        east_arrow_p1 = east_arrow_p0 + QPointF(
            -np.sin(-angle + np.pi / 3) * arrow_size,
            np.cos(-angle + np.pi / 3) * arrow_size)
        east_arrow_p2 = east_arrow_p0 + QPointF(
            -np.sin(-angle + np.pi - np.pi / 3) * arrow_size,
            np.cos(-angle + np.pi - np.pi / 3) * arrow_size)

        north_east_path = QPainterPath(north_point)
        north_east_path.lineTo(center_point)
        north_east_path.lineTo(east_point)

        north_east = self._scene.addPath(north_east_path, pen)

        pen = QPen(Color.TRANSPARENT, 0, Qt.SolidLine, Qt.SquareCap,
                   Qt.MiterJoin)
        pen.setCosmetic(True)

        north_arrow = self._scene.addPolygon(
            QPolygonF([north_arrow_p0, north_arrow_p1, north_arrow_p2]), pen,
            brush)
        east_arrow = self._scene.addPolygon(
            QPolygonF([east_arrow_p0, east_arrow_p1, east_arrow_p2]), pen,
            brush)

        north_textitem = OffsetedTextItem('N')
        north_textitem.setFont(font)
        north_textitem.setPos(north_point +
                              QPointF(north_line.unitVector().dx(),
                                      north_line.unitVector().dy()) * 1.5 *
                              arrow_size)
        north_textitem.setFlag(QGraphicsItem.ItemIgnoresTransformations)
        north_textitem.setBrush(brush)
        self._scene.addItem(north_textitem)
        north_textitem.setOffset(-north_textitem.boundingRect().width() / 2,
                                 -north_textitem.boundingRect().height() / 2)

        east_textitem = OffsetedTextItem('E')
        east_textitem.setFont(font)
        east_textitem.setPos(east_point +
                             QPointF(east_line.unitVector().dx(),
                                     east_line.unitVector().dy()) * 1.5 *
                             arrow_size)
        east_textitem.setFlag(QGraphicsItem.ItemIgnoresTransformations)
        east_textitem.setBrush(brush)
        self._scene.addItem(east_textitem)
        east_textitem.setOffset(-east_textitem.boundingRect().width() / 2,
                                -east_textitem.boundingRect().height() / 2)

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def addAxis(self, axis, alignment):
        super().addAxis(axis, alignment)

        axis.rangeChanged.connect(self.rangeChanged)

    def rangeChanged(self, min, max):
        if self.current_hovered_index is not None:
            return

        if self.pos is None:
            return

        pos_values = self.mapToValue(self.mapFromParent(self.pos))
        self.hovered.emit(None, pos_values.x(), pos_values.y())

    def mouseEvent(self, event):
        if self.current_hovered_index is not None:
            return

        if event.type() == QEvent.Leave:
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

    def pointHoveredEvent(self, point, state, series):
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

    def point_visible(self, series, index):
        for k, v in series.pointConfiguration(index).items():
            if k == QXYSeries.PointConfiguration.Visibility:
                return v

        return True

    def find_closest_point(self, point, points):
        closest_point = min(points,
                            key=lambda p: self.points_distance(p, point))
        closest_index = points.index(closest_point)

        return closest_point, closest_index

    def points_distance(self, point1, point2):
        diff = point2 - point1

        if isinstance(self.axisX(), QDateTimeAxis):
            x_max = self.axisX().max().toMSecsSinceEpoch()
            x_min = self.axisX().min().toMSecsSinceEpoch()
        else:
            x_max = self.axisX().max()
            x_min = self.axisX().min()

        x = diff.x() / (x_max-x_min)
        y = diff.y() / (self.axisY().max() - self.axisY().min())

        return x**2 + y**2


class KChartView(QChartView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setRenderHint(QPainter.Antialiasing)

        chart = KChart()
        chart.setMargins(QMargins(0, 0, 0, 0))
        chart.setBackgroundVisible(True)

        self.setStyleSheet("background: transparent")

        self.setChart(chart)

        self._value_pos = QPoint()
        self.setMouseTracking(True)

        self.vlines = []
        self.hlines = []

    def updateMinMax(self, y_min, y_max):
        self.chart().axisY().setRange(y_min, y_max)

    def drawForeground(self, painter, rect):
        super().drawForeground(painter, rect)

        painter.save()

        area = self.chart().plotArea()

        for x, color in self.vlines:
            pen = QPen(color, 0.5, Qt.DashLine, Qt.FlatCap, Qt.MiterJoin)
            painter.setPen(pen)

            pos = self.chart().mapToPosition(QPoint(x, 0))

            y1 = QPointF(pos.x(), area.top() + pen.width() / 2)
            y2 = QPointF(pos.x(), area.bottom() - pen.width() / 2)

            if area.left() <= pos.x() <= area.right():
                painter.drawLine(y1, y2)

        for y, color in self.hlines:
            pen = QPen(color, 1, Qt.SolidLine, Qt.FlatCap, Qt.MiterJoin)
            painter.setPen(pen)

            pos = self.chart().mapToPosition(QPointF(0, y))

            x1 = QPointF(area.left() + pen.width() / 2, pos.y())
            x2 = QPointF(area.right() - pen.width() / 2, pos.y())

            if area.left() <= pos.y() <= area.right():
                painter.drawLine(x1, x2)

        if not self._value_pos.isNull():
            pen = QPen(Color.GREY, 0.5, Qt.DashLine, Qt.FlatCap, Qt.MiterJoin)
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

    def resetVLines(self):
        self.vlines = []

    def resetHLines(self):
        self.hlines = []

    def addVLine(self, x, color):
        self.vlines.append((x, color))

    def addHLine(self, y, color):
        self.hlines.append((y, color))

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)

        if self.chart() is None:
            return

        self.chart().mouseEvent(event)

        pos = self.mapToScene(event.pos())

        if self.chart().plotArea().contains(pos):
            self._value_pos = pos
            self.setCursor(Qt.CrossCursor)
        else:
            self._value_pos = QPoint()
            self.unsetCursor()

        self.update()

    def event(self, event):
        if self.chart() is None:
            return super().event(event)

        if event.type() == QEvent.Leave:
            self._value_pos = QPoint()
            self.unsetCursor()

            self.chart().mouseEvent(event)

        return super().event(event)


class KDraggableChartView(KChartView):
    drag_max = 1
    drag_min = 0

    dragged = Signal(QAbstractSeries, float, float)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        chart = self.chart()

        chart.current_dragged_series = None
        chart.current_dragged_point = None
        chart.current_dragged_index = None

    def mouseMoveEvent(self, event):
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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def show(self):
        super().show()

        font_matrix = self.fontMetrics()
        width = font_matrix.boundingRect(self.informativeText()).width()

        spacer = QSpacerItem(width, 0, QSizePolicy.Minimum,
                             QSizePolicy.Expanding)
        self.layout().addItem(spacer,
                              self.layout().rowCount(), 0, 1,
                              self.layout().columnCount())


class KStatusIndicator(QGraphicsView):
    diameter = 100
    border = 8
    view = QRectF(0, 0, diameter, diameter)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._scene = QGraphicsScene()
        self.setScene(self._scene)

        self.setRenderHints(QPainter.Antialiasing |
                            QPainter.SmoothPixmapTransform)

        self.setStyleSheet("background: transparent")

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.pen = QPen(Color.GREY, self.border, Qt.SolidLine, Qt.SquareCap,
                        Qt.MiterJoin)
        self.brush = QBrush(Color.DARK_GREY, Qt.SolidPattern)

        self.ellipse = self._scene.addEllipse(0, 0, self.diameter,
                                              self.diameter, self.pen,
                                              self.brush)

        self.fitInView(self.view, Qt.KeepAspectRatio)

    def setStatus(self, color=Color.DARK_GREY, tooltip=''):
        self.brush.setColor(color)
        self.ellipse.setBrush(self.brush)
        self.setToolTip(f'Status: {tooltip}')

    def heightForWidth(self, width):
        return width

    def sizeHint(self):
        w = self.width()
        return QSize(w, self.heightForWidth(w))

    def resizeEvent(self, e):
        super().resizeEvent(e)

        self.fitInView(self.view, Qt.KeepAspectRatio)


class KColorbar(QGraphicsView):
    view = None
    margins = QMargins(0, 0, 0, 0)

    scale = LinearScale
    img_min = np.nan
    img_max = np.nan
    true_min = np.nan
    true_max = np.nan

    nb_ticks = 7
    margin = 75
    tick_length = 5
    tick_text_spacing = 5

    def __init__(self, parent=None):
        super().__init__(parent)

        self.scene = QGraphicsScene()
        self.setScene(self.scene)

        self.setRenderHints(QPainter.Antialiasing |
                            QPainter.SmoothPixmapTransform)

        self.setStyleSheet("background: transparent")
        self.setBackgroundBrush(QBrush(Color.TRANSPARENT))

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.ticks_group = self.scene.createItemGroup([])
        self.pixmap_item = self.scene.addPixmap(QPixmap())

        pen = QPen(Color.BLACK, 0.5, Qt.SolidLine, Qt.FlatCap, Qt.MiterJoin)
        pen.setCosmetic(True)

        self.border = self.scene.addRect(0, 0, 1, 1, pen)

    def draw_colorbar(self):
        colorbar_width = self.size().width() - self.margin

        scale = self.scale(0, 255)

        if self.img_min < self.true_min:
            i_min = 0
            colorbar_min = data_conversion.ndarray_normalize(
                self.true_min, self.img_min, self.img_max,
                colormap=self.colormap, scale=self.scale)
        else:
            i_min = scale.scale((self.img_min - self.true_min) /
                                (self.true_max - self.true_min) * 255)
            colorbar_min = data_conversion.ndarray_normalize(
                self.img_min, self.img_min, self.img_max,
                colormap=self.colormap, scale=self.scale)

        if self.img_max > self.true_max:
            i_max = 255
            colorbar_max = data_conversion.ndarray_normalize(
                self.true_max, self.img_min, self.img_max,
                colormap=self.colormap, scale=self.scale)
        else:
            i_max = scale.scale((self.img_max - self.true_min) /
                                (self.true_max - self.true_min) * 255)
            colorbar_max = data_conversion.ndarray_normalize(
                self.img_max, self.img_min, self.img_max,
                colormap=self.colormap, scale=self.scale)

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
                       img_uint8.shape[1], QImage.Format_Indexed8)
        image.setColorTable(self.colormap.table)

        self.pixmap = QPixmap.fromImage(image).scaled(colorbar_width, 256)
        self.pixmap_item.setPixmap(self.pixmap)

        self.view = self.pixmap.rect().adjusted(
            -self.margins.left(), -self.margins.top(), self.margins.right(),
            self.margins.bottom()).adjusted(0, -5, self.margin, 5)

        self.fitInView(self.view, Qt.IgnoreAspectRatio)

        self.border.setRect(self.pixmap_item.pixmap().rect())

        for item in self.ticks_group.childItems():
            self.scene.removeItem(item)
            self.ticks_group.removeFromGroup(item)

        pen = QPen(Color.BLACK, 0.5, Qt.SolidLine, Qt.FlatCap, Qt.MiterJoin)
        pen.setCosmetic(True)

        font = QFont()
        font.setPixelSize(10)

        for i in np.linspace(0, 255, self.nb_ticks):
            self.ticks_group.addToGroup(
                self.scene.addLine(colorbar_width, 255.5 - i, colorbar_width +
                                   self.tick_length, 255.5 - i, pen))

            v = scale.inverse(i) / 255 * (self.true_max -
                                          self.true_min) + self.true_min

            text_item = OffsetedTextItem(f'{v:3.3g}')
            text_item.setFont(font)
            text_item.setPos(
                colorbar_width + self.tick_length + self.tick_text_spacing,
                255.5 - i)
            text_item.setFlag(QGraphicsItem.ItemIgnoresTransformations)
            self.scene.addItem(text_item)
            self.ticks_group.addToGroup(text_item)

            probe = OffsetedTextItem(f'{v:3.3g}')  # TODO minus?
            probe.setFont(font)
            probe.setFlag(QGraphicsItem.ItemIgnoresTransformations)

            self.scene.addItem(probe)
            text_item.setOffset(
                0,
                probe.boundingRect().height() / 2 -
                text_item.boundingRect().height())
            self.scene.removeItem(probe)

    def setTrueMinMax(self, true_min, true_max):
        self.true_min = true_min
        self.true_max = true_max

        self.draw_colorbar()

    def setColormap(self, colormap):
        self.colormap = colormap

        self.draw_colorbar()

    def updateMinMax(self, img_min, img_max):
        self.img_min = img_min
        self.img_max = img_max

        self.draw_colorbar()

    def updateScale(self, scale):
        self.scale = scale

        self.draw_colorbar()

    def resizeEvent(self, e):
        super().resizeEvent(e)

        if self.view is not None:
            self.fitInView(self.view, Qt.IgnoreAspectRatio)
