import numpy as np

from PySide6.QtCharts import QChart, QChartView, QDateTimeAxis, QXYSeries
from PySide6.QtCore import (QEvent, QMargins, QPointF, QRect, QRectF, QSize,
                            Signal)
from PySide6.QtGui import QBrush, QFont, QIcon, QPainter, QPen, QPixmap, Qt
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (QDateTimeEdit, QDoubleSpinBox, QGraphicsItem,
                               QGraphicsScene, QGraphicsSimpleTextItem,
                               QGraphicsView, QLabel, QLineEdit,
                               QListWidgetItem, QMainWindow, QWidget)

from kalao.utils.image import LinearScale

from guis.kalao.definitions import Color, Logo
from guis.kalao.mixins import ArrayToImageMixin
from guis.kalao.string_formatter import KalAOFormatter


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
        return QRectF(b.x() - self.offset_x,
                      b.y() - self.offset_y, b.width(), b.height())


class KalAOLabel(QLabel, ArrayToImageMixin):
    pixmap_ = None
    text_format = None
    formatter = KalAOFormatter()

    def __init__(self, arg0=None, *args, **kwargs):
        super().__init__(arg0, *args, **kwargs)

        if isinstance(arg0, str):
            self.text_format = arg0

    def setPixmap(self, p):
        self.pixmap_ = p
        super().setPixmap(self.scaledPixmap())

    def heightForWidth(self, width):
        if self.pixmap_ is None:
            super().heightForWidth()
        else:
            return self.pixmap_.height() * width / self.pixmap_.width()

    def sizeHint(self):
        if self.pixmap_ is None:
            return super().sizeHint()
        else:
            w = self.width()
            return QSize(w, self.heightForWidth(w))

    def scaledPixmap(self):
        return self.pixmap_.scaled(self.size(), Qt.KeepAspectRatio,
                                   Qt.FastTransformation)

    def resizeEvent(self, e):
        if self.pixmap_ is not None:
            super().setPixmap(self.scaledPixmap())

    def setImage(self, img):
        self.prepare_array_for_qimage(img)

        self.setPixmap(QPixmap.fromImage(self.image))

    def setText(self, str):
        if self.text_format is None:
            self.text_format = str

        super().setText(str)

    def updateText(self, **kwargs):
        if self.text_format is None:
            self.text_format = self.text()

        self.setText(self.formatter.format(self.text_format, **kwargs))


class KalAOLineEdit(QLineEdit):
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


class KalAODateTimeEdit(QDateTimeEdit):
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


class KalAOScaledDoubleSpinbox(QDoubleSpinBox):
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

    def setScale(self, scale):
        super().setMinimum(super().minimum() / self.scale * scale)
        super().setMaximum(super().maximum() / self.scale * scale)
        super().setValue(super().value() / self.scale * scale)
        self.scale = scale


class KalAOSvgWidget(QSvgWidget):
    pass


class KalAOMainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowIcon(QIcon(str(Logo.ico)))

    def info_to_statusbar(self, string):
        if string:
            self.statusbar.showMessage(string)
        else:
            self.statusbar.clearMessage()


class KalAOWidget(QWidget):
    associated_stream = None
    opened = 0

    def __init__(self, *args, parent=None, **kwargs):
        super().__init__(parent)

        self.setWindowIcon(QIcon(str(Logo.ico)))
        self.resize(600, 400)
        self.move(50 + 50 * KalAOWidget.opened, 50 + 30 * KalAOWidget.opened)

        KalAOWidget.opened += 1


class KalAOListWidgetItem(QListWidgetItem):
    def __init__(self, key, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.key = key


class KalAOHoverableGraphicsScene(QGraphicsScene):
    x = np.nan
    y = np.nan

    hovered = Signal(float, float)
    clicked = Signal(float, float)
    scrolled = Signal(float, float, int)
    dragged = Signal(float, float, float, float)

    dragging = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def event(self, event):
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

            if event.pixelDelta().y() > 0:
                self.scrolled.emit(x, y, 1)
            elif event.pixelDelta().y() < 0:
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

    def pixmap_updated(self):
        if not (np.isnan(self.x) or np.isnan(self.y)):
            self.hovered.emit(self.x, self.y)


class KalAOGraphicsView(QGraphicsView, ArrayToImageMixin):
    img = None
    pixmap = None
    pixmap_item = None
    view = None
    margins = (0, 0, 0, 0)
    shape = (0, 0)

    tick_lines = []
    tick_labels = []

    hovered = Signal(int, int, float)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.scene = KalAOHoverableGraphicsScene()
        self.setScene(self.scene)

        self.setRenderHints(QPainter.Antialiasing |
                            QPainter.SmoothPixmapTransform)

        self.setStyleSheet("background: transparent")

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def viewSize(self):
        return self.view.adjusted(-self.margins[0], -self.margins[1],
                                  self.margins[2], self.margins[3])

    def heightForWidth(self, width):
        if self.pixmap is None:
            super().heightForWidth()
        else:
            return self.pixmap.height() * width / self.pixmap.width()

    def sizeHint(self):
        if self.pixmap is None:
            return super().sizeHint()
        else:
            w = self.width()
            return QSize(w, self.heightForWidth(w))

    def resizeEvent(self, e):
        super().resizeEvent(e)

        if self.view is not None:
            self.scene.setSceneRect(self.viewSize())
            self.fitInView(self.viewSize(), Qt.KeepAspectRatio)

    def setImage(self, img, img_min=None, img_max=None, scale=LinearScale,
                 view=None):
        if len(img.shape) < 2:
            img = img[np.newaxis, :]

        self.img = img
        self.img_min = img_min
        self.img_max = img_max
        self.scale = scale

        self.prepare_array_for_qimage(img, img_min, img_max, scale)

        self.pixmap = QPixmap.fromImage(self.image)

        if self.pixmap_item is None:
            self.pixmap_item = self.scene.addPixmap(self.pixmap)
            self.pixmap_item.setAcceptHoverEvents(True)
            self.scene.hovered.connect(self.hover_to_xyv)
        else:
            self.pixmap_item.setPixmap(self.pixmap)
            self.scene.pixmap_updated()

        if self.shape != img.shape and view is None:
            view = self.pixmap.rect()

        if view is not None:
            self.view = view
            self.scene.setSceneRect(self.viewSize())
            self.fitInView(self.viewSize(), Qt.KeepAspectRatio)
            self.shape = img.shape

    def updateColormap(self, colormap):
        self.colormap = colormap

        if self.image is not None:
            self.setImage(self.img, self.img_min, self.img_max, self.scale)

    def updateScale(self, scale):
        self.scale = scale

        if self.image is not None:
            self.setImage(self.img, self.img_min, self.img_max, self.scale)

    def updateMinMax(self, img_min, img_max):
        self.img_min = img_min
        self.img_max = img_max

        if self.image is not None:
            self.setImage(self.img, self.img_min, self.img_max, self.scale)

    def setView(self, shape):
        self.view = QRect(0, 0, shape[1], shape[0])
        self.scene.setSceneRect(self.viewSize())
        self.fitInView(self.viewSize(), Qt.KeepAspectRatio)

    def hover_to_xyv(self, x, y):
        if not (np.isnan(x) or np.isnan(y)):
            x = int(x)
            y = int(y)
        else:
            self.hovered.emit(-1, -1, np.nan)

        if 0 <= y < self.img.shape[0] and 0 <= x < self.img.shape[1]:
            self.hovered.emit(x, y, self.img[y, x])
        else:
            self.hovered.emit(-1, -1, np.nan)

    def addTicks(self, spacing, length, text_spacing, fontsize, ticks_x,
                 ticks_y):
        self.margins = (spacing + length + text_spacing + 4*fontsize + 50,
                        spacing + length + text_spacing + 4*fontsize,
                        spacing + length + text_spacing + 4*fontsize + 50,
                        spacing + length + text_spacing + 4*fontsize)

        for line_item in self.tick_lines:
            self.scene.removeItem(line_item)

        self.tick_lines = []

        width = self.view.width()
        height = self.view.height()

        pen = QPen(Color.GREY, 1.25, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin)
        pen.setCosmetic(True)

        self.addVerticalTicks(0, height, -(spacing), -(spacing + length), pen,
                              ticks_y)
        self.addVerticalTicks(0, height, width + spacing,
                              width + spacing + length, pen, ticks_y)

        self.addHorizontalTicks(0, width, -(spacing), -(spacing + length), pen,
                                ticks_x)
        self.addHorizontalTicks(0, width, height + spacing,
                                height + spacing + length, pen, ticks_x)

    def addVerticalTicks(self, start, end, tick_start, tick_end, pen, ticks_y):
        self.tick_lines.append(
            self.scene.addLine(tick_start, start, tick_start, end, pen))

        self.tick_lines.append(
            self.scene.addLine(tick_start, start, tick_end, start, pen))
        self.tick_lines.append(
            self.scene.addLine(tick_start, end, tick_end, end, pen))

        for y, label in ticks_y:
            self.tick_lines.append(
                self.scene.addLine(tick_start, y, tick_end, y, pen))

    def addHorizontalTicks(self, start, end, tick_start, tick_end, pen,
                           ticks_x):
        self.tick_lines.append(
            self.scene.addLine(start, tick_start, end, tick_start, pen))

        self.tick_lines.append(
            self.scene.addLine(start, tick_start, start, tick_end, pen))
        self.tick_lines.append(
            self.scene.addLine(end, tick_start, end, tick_end, pen))

        for x, label in ticks_x:
            self.tick_lines.append(
                self.scene.addLine(x, tick_start, x, tick_end, pen))

    def addTicksLabels(self, spacing, length, text_spacing, fontsize, ticks_x,
                       ticks_y):
        for text_item in self.tick_labels:
            self.scene.removeItem(text_item)

        self.tick_labels = []

        width = self.view.width()
        height = self.view.height()

        font = QFont()
        font.setPixelSize(fontsize)

        self.addVerticalTickLabels(width + spacing + length + text_spacing,
                                   font, ticks_y)
        self.addHorizontalTickLabels(height + spacing + length + text_spacing,
                                     font, ticks_x)

    def addVerticalTickLabels(self, text_start, font, ticks_y):
        for y, label in ticks_y:
            text_item = OffsetedTextItem(label)
            text_item.setFont(font)
            text_item.setPos(text_start, y)
            text_item.setFlag(QGraphicsItem.ItemIgnoresTransformations)
            self.scene.addItem(text_item)

            if not label.startswith('-'):
                label = '-' + label

            probe = OffsetedTextItem(label)
            probe.setFont(font)
            probe.setFlag(QGraphicsItem.ItemIgnoresTransformations)

            self.scene.addItem(probe)
            text_item.setOffset(
                text_item.boundingRect().width() -
                probe.boundingRect().width(),
                text_item.boundingRect().height() / 2)
            self.scene.removeItem(probe)

            self.tick_labels.append(text_item)

    def addHorizontalTickLabels(self, text_start, font, ticks_x):
        for x, label in ticks_x:
            text_item = OffsetedTextItem(label)
            text_item.setFont(font)
            text_item.setPos(x, text_start)
            text_item.setFlag(QGraphicsItem.ItemIgnoresTransformations)
            self.scene.addItem(text_item)

            label = label.removeprefix('-')

            probe = OffsetedTextItem(label)
            probe.setFont(font)
            probe.setFlag(QGraphicsItem.ItemIgnoresTransformations)

            self.scene.addItem(probe)
            text_item.setOffset(
                text_item.boundingRect().width() -
                probe.boundingRect().width() / 2, 0)
            self.scene.removeItem(probe)

            self.tick_labels.append(text_item)


class KalAOChart(QChart):
    hovered = Signal(float, float)

    point_size = 3
    current_hovered_index = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def pointHoveredEvent(self, point, state, series):
        points = series.points()

        closest_point, closest_index = self.find_closest_point(point, points)

        if self.current_hovered_index is not None:
            series.setPointConfiguration(self.current_hovered_index, {
                QXYSeries.PointConfiguration.Size: self.point_size
            })

        if not self.point_visible(series, closest_index):
            return

        if state:
            series.setPointConfiguration(closest_index, {
                QXYSeries.PointConfiguration.Size: 2 * self.point_size
            })

            self.hovered.emit(closest_point.x(), closest_point.y())
        else:
            series.setPointConfiguration(closest_index, {
                QXYSeries.PointConfiguration.Size: self.point_size
            })

            self.hovered.emit(np.nan, np.nan)

        self.current_hovered_index = closest_index

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


class KalAOChartView(QChartView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setRenderHint(QPainter.Antialiasing)

        self.chart = KalAOChart()
        self.chart.setMargins(QMargins(0, 0, 0, 0))

        self.chart.setBackgroundVisible(False)
        self.setStyleSheet("background: transparent")

        self.setChart(self.chart)

    def updateMinMax(self, y_min, y_max):
        self.chart.axisY().setRange(y_min, y_max)


class KalAODraggableChartView(KalAOChartView):
    drag_max = 1
    drag_min = 0

    dragged = Signal(float, float)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.chart.current_dragged_series = None
        self.chart.current_dragged_point = None
        self.chart.current_dragged_index = None

    def mouseMoveEvent(self, event):
        if self.chart.current_dragged_index is not None:
            pos = self.chart.mapToValue(event.pos(),
                                        self.chart.current_dragged_series)

            x = self.chart.current_dragged_point.x()
            y = max(min(pos.y(), self.drag_max), self.drag_min)

            self.chart.current_dragged_series.replace(
                self.chart.current_dragged_index, QPointF(x, y))

            self.dragged.emit(x, y)

        super().mouseMoveEvent(event)


class KalAOStatusIndicator(QGraphicsView):
    diameter = 100
    border = 8
    view = QRectF(0, 0, diameter, diameter)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setToolTipDuration(2147483647)

        self.scene = QGraphicsScene()
        self.setScene(self.scene)

        self.setRenderHints(QPainter.Antialiasing |
                            QPainter.SmoothPixmapTransform)

        self.setStyleSheet("background: transparent")

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.pen = QPen(Color.GREY, self.border, Qt.SolidLine, Qt.SquareCap,
                        Qt.MiterJoin)
        self.brush = QBrush(Color.DARK_GREY, Qt.SolidPattern)

        self.ellipse = self.scene.addEllipse(0, 0, self.diameter,
                                             self.diameter, self.pen,
                                             self.brush)

        self.fitInView(self.view, Qt.KeepAspectRatio)

    def setStatus(self, color=Color.DARK_GREY, tooltip=''):
        self.brush.setColor(color)
        self.ellipse.setBrush(self.brush)
        self.setToolTip(str(tooltip))

    def heightForWidth(self, width):
        return width

    def sizeHint(self):
        w = self.width()
        return QSize(w, self.heightForWidth(w))

    def resizeEvent(self, e):
        super().resizeEvent(e)

        self.fitInView(self.view, Qt.KeepAspectRatio)
