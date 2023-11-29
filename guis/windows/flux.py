from PySide2.QtGui import Qt

from guis.kalao import colormaps
from guis.kalao.mixins import HoverMixin, MinMaxMixin
from guis.kalao.ui_loader import loadUi
from guis.kalao.widgets import KalAOWidget

import config


class FluxWidget(KalAOWidget, MinMaxMixin, HoverMixin):
    associated_stream = config.Streams.FLUX
    stream_info = config.StreamInfo.shwfs_slopes_flux
    data_unit = ' ADU'
    data_precision = 0

    axis_unit = ' px'
    axis_precision = 0

    def __init__(self, backend, parent=None):
        super().__init__(parent)

        self.backend = backend

        loadUi('flux.ui', self)
        self.resize(600, 400)

        MinMaxMixin.__init__(self)

        self.change_colormap(Qt.Unchecked)

        self.flux_view.hovered.connect(self.hover_event)
        backend.updated.connect(self.data_updated)

    def data_updated(self):
        img = self.backend.data['shwfs_slopes_flux']['stream']
        flux_avg = self.backend.data['shwfs_slopes_flux'][
            'flux_subaperture_avg']
        flux_brightest = self.backend.data['shwfs_slopes_flux'][
            'flux_subaperture_brightest']

        if self.autoscale_checkbox.isChecked():
            img_min = img.min()
            img_max = img.max()

            self.min_spinbox.setValue(img_min)
            self.max_spinbox.setValue(img_max)
        else:
            img_min = self.data_min
            img_max = self.data_max

        self.flux_view.setImage(img, img_min, img_max)

        self.flux_avg_label.updateText(flux_avg=flux_avg, unit=self.data_unit)
        self.flux_brightest_label.updateText(flux_brightest=flux_brightest,
                                             unit=self.data_unit)

    def change_colormap(self, state):
        if state == Qt.Checked:
            self.flux_view.setColormap(colormaps.GrayscaleSaturation())
        else:
            self.flux_view.setColormap(colormaps.BlackBody())
