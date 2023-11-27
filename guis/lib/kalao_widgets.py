from enum import Enum

import numpy as np

from PySide2.QtCharts import QtCharts
from PySide2.QtCore import QEvent, QMargins, QPointF, QRectF, QSize, Signal
from PySide2.QtGui import QColor, QImage, QPainter, QPixmap, Qt
from PySide2.QtWidgets import (QGraphicsScene, QGraphicsSimpleTextItem,
                               QGraphicsView, QLabel, QWidget)

from . import colormaps

grayscale_with_clip_colormap = []
grayscale_with_clip_colormap.append(QColor(0, 0, 255).rgb())
for i in range(1, 255):
    grayscale_with_clip_colormap.append(QColor(i, i, i).rgb())
grayscale_with_clip_colormap.append(QColor(255, 0, 0).rgb())


class Color():
    BLACK = QColor('#000000')
    DARK_GREY = QColor('#666666')
    GREY = QColor('#eeeeee')
    WHITE = QColor('#ffffff')

    RED = QColor('#ed1515')
    ORANGE = QColor('#f67400')
    GREEN = QColor('#11d116')
    BLUE = QColor('#1d99f3')
    YELLOW = QColor('#fdbc4b')


class ArrayToImageMixin():
    colormap = colormaps.Hot()

    def prepare_array_for_qimage(self, img, img_min=None, img_max=None):
        if img_min is None:
            img_min = img.min()

        if img_max is None:
            img_max = img.max()

        delta = img_max - img_min
        delta = max(1e-9, delta)

        scale_max = 255
        scale_min = 0

        if self.colormap.has_transparency:
            scale_max -= 1

        if self.colormap.color_saturation_high is not None:
            scale_max -= 0.51

        if self.colormap.color_saturation_low is not None:
            scale_min += 0.51

        rescale = (scale_max-scale_min) / delta
        offset = img_min*rescale - scale_min

        array = img*rescale - offset
        array = np.rint(array).astype(int)
        array = np.clip(array, 0, 255)

        self.img_uint8 = np.require(array, np.uint8, 'C')
        self.image = QImage(self.img_uint8.data, self.img_uint8.shape[1],
                            self.img_uint8.shape[0], self.img_uint8.shape[1],
                            QImage.Format_Indexed8)
        self.image.setColorTable(self.colormap.colormap)


class MinMaxMixin:
    data_min = -np.inf
    data_max = np.inf
    data_unit = ''
    data_scaling = 1
    data_scaling_prev = 1
    data_precision = 0
    data_center_x = 0
    data_center_y = 0

    axis_unit = ''
    axis_scaling = 1
    axis_precision = 0

    def __init__(self):
        self.min_spinbox.valueChanged.connect(self.min_changed)
        self.max_spinbox.valueChanged.connect(self.max_changed)
        self.autoscale_checkbox.stateChanged.connect(self.autoscale_changed)
        self.reset_button.clicked.connect(self.reset_clicked)

        self.autoscale_changed(self.autoscale_checkbox.checkState())
        self.min_changed(self.min_spinbox.value())
        self.max_changed(self.max_spinbox.value())
        self.update_spinboxes_unit()

    def min_changed(self, d):
        self.data_min = d
        self.max_spinbox.setMinimum(d)

    def max_changed(self, d):
        self.data_max = d
        self.min_spinbox.setMaximum(d)

    def autoscale_changed(self, state):
        self.min_spinbox.setEnabled(state == Qt.Unchecked)
        self.max_spinbox.setEnabled(state == Qt.Unchecked)

    def reset_clicked(self, checked):
        self.autoscale_checkbox.setChecked(False)
        self.min_spinbox.setValue(self.stream_info['min'] * self.data_scaling)
        self.max_spinbox.setValue(self.stream_info['max'] * self.data_scaling)

    def update_spinboxes_unit(self):
        self.min_spinbox.setValue(self.min_spinbox.value() *
                                  self.data_scaling / self.data_scaling_prev)
        self.max_spinbox.setValue(self.max_spinbox.value() *
                                  self.data_scaling / self.data_scaling_prev)

        self.min_spinbox.setSuffix(self.data_unit)
        self.max_spinbox.setSuffix(self.data_unit)

        self.data_scaling_prev = self.data_scaling


class HoverMixin():
    hovered = Signal(str)

    def __init__(self, view):
        self.view = view

    def hover_event(self, x, y):
        img = self.img

        if 0 <= y < img.shape[0] and 0 <= x < img.shape[1]:
            string = f'X: {(x-self.data_center_x)*self.axis_scaling:.{self.axis_precision}f}{self.axis_unit}, Y: {(y-self.data_center_y)*self.axis_scaling:.{self.axis_precision}f}{self.axis_unit}, V: {img[y,x]:.{self.data_precision}f}{self.data_unit}'

            self.hovered.emit(string)
        else:
            self.hovered.emit('')


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setScaledContents(False)

    def setPixmap(self, p):
        self.pixmap_ = p
        super().setPixmap(self.scaledPixmap())

    def heightForWidth(self, width):
        if self.pixmap_ is None:
            return self.height()
        else:
            return self.pixmap_.height() * width / self.pixmap_.width()

    def sizeHint(self):
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


class KalAOWidget(QWidget):
    associated_stream = None
    opened = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.move(100 + 50 * KalAOWidget.opened, 100 + 30 * KalAOWidget.opened)

        KalAOWidget.opened += 1


class HoverScene(QGraphicsScene):
    x = -1
    y = -1

    hovered = Signal(int, int, QPointF)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def event(self, event):
        if event.type() == QEvent.Type.GraphicsSceneMouseMove:
            self.x = int(event.scenePos().x())
            self.y = int(event.scenePos().y())
            self.screenPos = event.screenPos()

            self.hovered.emit(self.x, self.y, event.screenPos())

            return True

        elif event.type() == QEvent.Type.Leave:
            self.x = -1
            self.y = -1

            self.hovered.emit(self.x, self.y, None)

            return True

        elif event.type() == QEvent.Type.Enter:
            return True

        else:
            return super().event(event)

    def pixmap_updated(self):
        if self.x != -1 and self.y != -1:
            self.hovered.emit(self.x, self.y, self.screenPos)


class KalAOGraphicsView(QGraphicsView, ArrayToImageMixin):
    img = None
    pixmap = None
    pixmap_item = None
    margins = (1, 1, 1, 1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.scene = HoverScene()
        self.setScene(self.scene)

        self.setStyleSheet("background: transparent")

    def viewSize(self):
        return self.pixmap.rect().adjusted(-self.margins[0], -self.margins[1],
                                           self.margins[2], self.margins[3])

    def resizeEvent(self, e):
        super().resizeEvent(e)

        if self.pixmap is not None:
            self.fitInView(self.viewSize(), Qt.KeepAspectRatio)

    def setImage(self, img, img_min=None, img_max=None):
        self.prepare_array_for_qimage(img, img_min, img_max)

        self.pixmap = QPixmap.fromImage(self.image)

        if self.pixmap_item is None:
            self.pixmap_item = self.scene.addPixmap(self.pixmap)
            self.pixmap_item.setAcceptHoverEvents(True)

            self.fitInView(self.viewSize(), Qt.KeepAspectRatio)
        else:
            self.pixmap_item.setPixmap(self.pixmap)
            self.scene.pixmap_updated()

        #TODO: only on shape change
        #self.fitInView(self.viewSize(), Qt.KeepAspectRatio)


class KalAOChart(QtCharts.QChartView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setRenderHint(QPainter.Antialiasing)

        self.chart = QtCharts.QChart()
        self.chart.setMargins(QMargins(0, 0, 0, 0))
        self.chart.setBackgroundVisible(False)

        self.setChart(self.chart)
