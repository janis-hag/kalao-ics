import numpy as np

from PySide6.QtCore import QRectF, Slot
from PySide6.QtGui import QPen, Qt

from kalao.utils import image

from guis.kalao import colormaps
from guis.kalao.definitions import Color, Scale
from guis.kalao.mixins import BackendDataMixin, MinMaxMixin, SceneHoverMixin
from guis.kalao.ui_loader import loadUi
from guis.kalao.widgets import KalAOMainWindow

import config


class FLIZoomWindow(KalAOMainWindow, MinMaxMixin, SceneHoverMixin,
                    BackendDataMixin):
    associated_stream = config.Streams.FLI
    stream_info = config.StreamInfo.fli_stream

    data_unit = ' ADU'
    data_precision = 0
    data_center_x = config.FLI.center_x
    data_center_y = config.FLI.center_y

    axis_unit = ' px'
    axis_precision = 0
    axis_scaling = 1

    zoom_center_x = 512
    zoom_center_y = 512
    zoom_level = 1

    last_img = None

    def __init__(self, backend, img, parent=None):
        super().__init__(parent)

        self.backend = backend
        self.img = img

        loadUi('fli_zoom.ui', self)
        self.resize(600, 400)

        self.init_minmax([self.fli_view, self.zoom_view])

        for colormap in colormaps.get_all_colormaps():
            self.colormap_combobox.addItem(colormap.__name__, colormap)

        colormap = self.colormap_combobox.currentData()()
        self.fli_view.updateColormap(colormap)
        self.zoom_view.updateColormap(colormap)

        for scale in Scale:
            self.scale_combobox.addItem(scale.value, scale)

        pen = QPen(Color.YELLOW, 1, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin)
        pen.setCosmetic(True)

        self.roi = self.fli_view.scene.addRect(0, 0, 1024, 1024, pen)
        self.roi.setZValue(1)

        self.update_fli(img)

        self.fli_view.hovered.connect(self.hover_xyv_to_str)
        self.zoom_view.hovered.connect(self.hover_xyv_to_str_zoom)

        self.fli_view.scene.clicked.connect(self.fli_clicked)
        self.fli_view.scene.scrolled.connect(self.fli_scrolled)

        self.zoom_view.scene.clicked.connect(self.zoom_clicked)
        self.zoom_view.scene.scrolled.connect(self.zoom_scrolled)

        self.star_label.updateText(x=np.nan, y=np.nan, peak=np.nan,
                                   fwhm=np.nan, precision=np.nan,
                                   data_unit=self.data_unit,
                                   axis_unit=self.axis_unit)

        self.hovered.connect(self.info_to_statusbar)
        backend.fli_updated.connect(self.fli_updated)

        self.show()

    def fli_updated(self, data):
        img = self.consume_stream(data, config.Streams.FLI)

        if img is not None:
            if self.update_checkbox.checkState() == Qt.Checked:
                self.update_fli(img)
            else:
                self.last_img = img

    @Slot(int)
    def on_colormap_combobox_currentIndexChanged(self, index):
        colormap = self.colormap_combobox.currentData()()
        self.fli_view.updateColormap(colormap)
        self.zoom_view.updateColormap(colormap)

    @Slot(int)
    def on_scale_combobox_currentIndexChanged(self, index):
        scale = self.scale_combobox.currentData()
        self.fli_view.updateScale(scale)
        self.zoom_view.updateScale(scale)

    @Slot(int)
    def on_update_checkbox_stateChanged(self, state):
        if Qt.CheckState(state) == Qt.Checked:
            if self.last_img is not None:
                self.update_fli(self.last_img)

    def hover_xyv_to_str_zoom(self, x, y, v):
        if x != -1 and y != -1:
            x, y = self.xy_to_zoom_xy(x, y)

            string = f'X: {(x-self.data_center_x)*self.axis_scaling:.{self.axis_precision}f}{self.axis_unit}, Y: {(y-self.data_center_y)*self.axis_scaling:.{self.axis_precision}f}{self.axis_unit}, V: {v*self.data_scaling:.{self.data_precision}f}{self.data_unit}'

            self.hovered.emit(string)
        else:
            self.hovered.emit('')

    def fli_clicked(self, x, y):
        self.zoom_center_x = x
        self.zoom_center_y = y

        self.update_zoom()

    def fli_scrolled(self, x, y, z):
        self.zoom_center_x = x
        self.zoom_center_y = y

        if z > 0:
            self.zoom_level *= 2
        else:
            self.zoom_level //= 2

            if self.zoom_level < 1:
                self.zoom_level = 1

        self.update_zoom()

    def zoom_clicked(self, x, y):
        x, y = self.xy_to_zoom_xy(x, y)

        self.zoom_center_x = x
        self.zoom_center_y = y

        self.update_zoom()

    def zoom_scrolled(self, x, y, z):
        hw = 1024 // self.zoom_level // 2

        fx = (x - self.view_shift_x) / hw - 1
        fy = (y - self.view_shift_y) / hw - 1

        x, y = self.xy_to_zoom_xy(x, y)

        if z > 0:
            self.zoom_level *= 2

            self.zoom_center_x = int(x - fx*hw/2)
            self.zoom_center_y = int(y - fy*hw/2)
        else:
            self.zoom_level //= 2

            self.zoom_center_x = int(x - fx*hw*2)
            self.zoom_center_y = int(y - fy*hw*2)

            if self.zoom_level < 1:
                self.zoom_level = 1

        self.update_zoom()

    def xy_to_zoom_xy(self, x, y):
        return self.zoom_center_x - 1024 // self.zoom_level // 2 + x - self.view_shift_x, self.zoom_center_y - 1024 // self.zoom_level // 2 + y - self.view_shift_y

    def update_fli(self, img):
        self.img = img
        self.last_img = None

        img_min, img_max = self.compute_min_max(self.img)

        self.fli_view.setImage(self.img, img_min, img_max,
                               self.scale_combobox.currentData())

        # x, y, peak, fwhm = starfinder.find_star(img) #TODO
        x, y, peak, fwhm = np.nan, np.nan, np.nan, np.nan

        self.star_label.updateText(x=x * self.axis_scaling,
                                   y=y * self.axis_scaling,
                                   peak=peak * self.data_scaling,
                                   fwhm=fwhm * self.axis_scaling,
                                   precision=self.axis_precision,
                                   data_unit=self.data_unit,
                                   axis_unit=self.axis_unit)

        self.update_zoom()

    def update_zoom(self):
        x = self.zoom_center_x
        y = self.zoom_center_y
        hw = 1024 // self.zoom_level // 2

        self.x_spinbox.setValue(x - self.data_center_x)
        self.y_spinbox.setValue(y - self.data_center_y)
        self.zoom_spinbox.setValue(self.zoom_level)
        self.roi.setRect(x - hw, y - hw, 2 * hw, 2 * hw)

        zoom = image.cut(self.img, 2 * hw, [y, x], overflow='cut')

        if x - hw < 0:
            self.view_shift_x = zoom.shape[1] - 2*hw
        else:
            self.view_shift_x = 0

        if y - hw < 0:
            self.view_shift_y = zoom.shape[0] - 2*hw
        else:
            self.view_shift_y = 0

        self.zoom_view.setImage(
            zoom, self.min_spinbox.value(), self.max_spinbox.value(),
            self.scale_combobox.currentData(),
            view=QRectF(self.view_shift_x, self.view_shift_y, 2 * hw, 2 * hw))
