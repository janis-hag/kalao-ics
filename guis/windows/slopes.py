import numpy as np

from PySide6.QtGui import Qt

from kalao.utils import kalao_tools

from guis.kalao import colormaps
from guis.kalao.mixins import BackendDataMixin, MinMaxMixin, SceneHoverMixin
from guis.kalao.ui_loader import loadUi
from guis.kalao.widgets import KalAOWidget

import config


class SlopesWidget(KalAOWidget, MinMaxMixin, SceneHoverMixin,
                   BackendDataMixin):
    associated_stream = config.Streams.SLOPES
    stream_info = config.StreamInfo.shwfs_slopes

    data_unit = ' px'
    data_precision = 3

    axis_unit = ' px'
    axis_precision = 0

    def __init__(self, backend, parent=None):
        super().__init__(parent)

        self.backend = backend
        self.mask = kalao_tools.generate_slopes_mask_from_subaps(
            config.AO.masked_subaps)

        loadUi('slopes.ui', self)
        self.resize(600, 400)

        self.init_minmax(self.slopes_view, symetric=True)

        self.change_units(Qt.Unchecked)
        self.change_colormap(Qt.Unchecked)

        self.tip_label.updateText(tip=np.nan, unit=self.data_unit)
        self.tilt_label.updateText(tilt=np.nan, unit=self.data_unit)
        self.residual_label.updateText(residual=np.nan, unit=self.data_unit)

        self.slopes_view.hovered.connect(self.hover_xyv_to_str)
        backend.streams_updated.connect(self.streams_updated)

    def streams_updated(self, data):
        img = self.consume_stream(data, config.Streams.SLOPES)

        if img is not None:
            img = np.ma.masked_array(img, mask=self.mask, fill_value=0)

            img_min, img_max = self.compute_min_max(img)

            self.slopes_view.setImage(img, img_min, img_max)

        slope_x = self.consume_param(data, config.FPS.SHWFS, 'slope_x')
        if slope_x is not None:
            self.tip_label.updateText(tip=slope_x * self.data_scaling,
                                      unit=self.data_unit)

        slope_y = self.consume_param(data, config.FPS.SHWFS, 'slope_y')
        if slope_y is not None:
            self.tilt_label.updateText(tilt=slope_y * self.data_scaling,
                                       unit=self.data_unit)

        residual = self.consume_param(data, config.FPS.SHWFS, 'residual')
        if residual is not None:
            self.residual_label.updateText(
                residual=residual * self.data_scaling, unit=self.data_unit)

    def change_units(self, state):
        if Qt.CheckState(state) == Qt.Checked:
            self.update_spinboxes_unit(' asec', config.WFS.plate_scale)
        else:
            self.update_spinboxes_unit(' px', 1)

    def change_colormap(self, state):
        if Qt.CheckState(state) == Qt.Checked:
            self.slopes_view.updateColormap(
                colormaps.GrayscaleSaturationTransparent())
        else:
            self.slopes_view.updateColormap(colormaps.CoolWarmTransparent())
