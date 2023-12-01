from subprocess import Popen

import numpy as np

from PySide2.QtGui import QFont, QPen, Qt
from PySide2.QtWidgets import QGraphicsItem

from guis.kalao import colormaps
from guis.kalao.definitions import Color
from guis.kalao.mixins import HoverMixin, MinMaxMixin
from guis.kalao.ui_loader import loadUi
from guis.kalao.widgets import KalAOMainWindow, OffsetedTextItem

import config


class FLIZoomWindow(KalAOMainWindow, MinMaxMixin, HoverMixin):
    associated_stream = config.Streams.FLI
    stream_info = config.StreamInfo.fli_stream
    data_unit = ' ADU'
    data_precision = 0

    axis_unit = ' px'
    axis_precision = 0
    axis_scaling = 1

    def __init__(self, img, parent=None):
        super().__init__(parent)

        self.img = img

        loadUi('fli_zoom.ui', self)
        self.resize(600, 400)

        MinMaxMixin.__init__(self)

        self.fli_view.setImage(img)

        self.show()