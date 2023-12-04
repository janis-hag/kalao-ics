import numpy as np

from PySide6.QtCharts import QChart, QChartView
from PySide6.QtCore import QEvent, QMargins, QPointF, QRectF, QSize, Signal
from PySide6.QtGui import QIcon, QPainter, QPixmap, Qt
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (QDateTimeEdit, QGraphicsScene,
                               QGraphicsSimpleTextItem, QGraphicsView, QLabel,
                               QListWidgetItem, QMainWindow, QWidget)

from guis.kalao.definitions import Logo
from guis.kalao.mixins import ArrayToImageMixin


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

        self.setText(self.text_format.format(**kwargs))


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


class KalAOSvgWidget(QSvgWidget):
    pass


class KalAOMainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowIcon(QIcon(str(Logo.ico)))


class KalAOWidget(QWidget):
    associated_stream = None
    opened = 0

    def __init__(self, *args, parent=None, **kwargs):
        super().__init__(parent)

        self.setWindowIcon(QIcon(str(Logo.ico)))
        self.resize(600, 400)
        self.move(100 + 50 * KalAOWidget.opened, 100 + 30 * KalAOWidget.opened)

        KalAOWidget.opened += 1


class KalAOListWidgetItem(QListWidgetItem):
    def __init__(self, key, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.key = key


class HoverScene(QGraphicsScene):
    x = -1
    y = -1

    hovered = Signal(int, int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def event(self, event):
        if event.type() == QEvent.Type.GraphicsSceneMouseMove:
            self.x = int(event.scenePos().x())
            self.y = int(event.scenePos().y())

            self.hovered.emit(self.x, self.y)

            return True

        elif event.type() == QEvent.Type.GraphicsSceneLeave:
            self.x = -1
            self.y = -1

            self.hovered.emit(self.x, self.y)

            return True

        elif event.type() == QEvent.Type.GraphicsSceneHoverEnter:
            return True

        else:
            return super().event(event)

    def pixmap_updated(self):
        if self.x != -1 and self.y != -1:
            self.hovered.emit(self.x, self.y)


class KalAOGraphicsView(QGraphicsView, ArrayToImageMixin):
    img = None
    pixmap = None
    pixmap_item = None
    margins = (0, 0, 0, 0)
    shape = (0, 0)

    hovered = Signal(int, int, float)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.scene = HoverScene()
        self.setScene(self.scene)

        self.setStyleSheet("background: transparent")

    def viewSize(self):
        return self.pixmap.rect().adjusted(-self.margins[0], -self.margins[1],
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

        if self.pixmap is not None:
            self.fitInView(self.viewSize(), Qt.KeepAspectRatio)

    def setImage(self, img, img_min=None, img_max=None):
        self.img = img

        self.prepare_array_for_qimage(img, img_min, img_max)

        self.pixmap = QPixmap.fromImage(self.image)

        if self.pixmap_item is None:
            self.pixmap_item = self.scene.addPixmap(self.pixmap)
            self.pixmap_item.setAcceptHoverEvents(True)
            self.scene.hovered.connect(self.hover_event)
        else:
            self.pixmap_item.setPixmap(self.pixmap)
            self.scene.pixmap_updated()

        if self.shape != img.shape:
            self.fitInView(self.viewSize(), Qt.KeepAspectRatio)
            self.adjustSize()
            self.shape = img.shape

    def setColormap(self, colormap):
        self.colormap = colormap

        if self.image is not None:
            self.image.setColorTable(self.colormap.colormap)
            self.pixmap = QPixmap.fromImage(self.image)
            self.pixmap_item.setPixmap(self.pixmap)

    def hover_event(self, x, y):
        if 0 <= y < self.img.shape[0] and 0 <= x < self.img.shape[1]:
            self.hovered.emit(x, y, self.img[y, x])
        else:
            self.hovered.emit(-1, -1, np.nan)


class KalAOChart(QChartView):
    drag_max = 1
    drag_min = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setRenderHint(QPainter.Antialiasing)

        self.chart = QChart()
        self.chart.setMargins(QMargins(0, 0, 0, 0))

        self.chart.setBackgroundVisible(False)
        self.setStyleSheet("background: transparent")

        self.setChart(self.chart)

        self.chart.current_series = None
        self.chart.current_point = None
        self.chart.current_index = None

    def mouseMoveEvent(self, event):
        if self.chart.current_index is not None:
            pos = self.chart.mapToValue(event.pos(), self.chart.current_series)

            y = max(min(pos.y(), self.drag_max), self.drag_min)

            self.chart.current_series.replace(
                self.chart.current_index,
                QPointF(self.chart.current_point.x(), y))

        super().mouseMoveEvent(event)
