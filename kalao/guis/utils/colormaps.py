import inspect
import sys

import numpy as np
import pandas as pd

from PySide6.QtGui import QColor, QImage, QPixmap, Qt
from PySide6.QtWidgets import QApplication, QLabel, QSizePolicy, QStyle

import config

colormaps_path = config.kalao_ics_path / 'colormaps'

# See https://www.kennethmoreland.com/color-advice/


class Colormap:
    table = None

    saturation_low_color = None
    saturation_high_color = None
    has_transparency = False

    min = 0
    max = 255

    no_data_value = min
    transparency_value = max
    saturation_low_value = min
    saturation_high_value = max


class ColormapExtrapolated(Colormap):
    colors = None

    def __init__(self, start=0, end=255, color_max=255):
        length = len(self.colors)

        if self.has_transparency:
            self.transparency_value = end
            self.max = end - 1
            end -= 1

        if self.saturation_low_color is not None:
            self.saturation_low_value = start
            self.min = start + 1
            start += 1

        if self.saturation_high_color is not None:
            self.saturation_high_value = end
            self.max = end - 1
            end -= 1

        limits = []
        for i in range(length):
            limits.append(start + i * (end-start) / (length-1))

        self.table = []
        j = 0

        if self.saturation_low_color is not None:
            self.table.append(
                QColor(self.saturation_low_color[0] * color_max,
                       self.saturation_low_color[1] * color_max,
                       self.saturation_low_color[2] * color_max).rgba())

        for i in range(start, end + 1):
            if i > limits[j + 1]:
                j += 1

            coeff = (i - limits[j]) / (limits[j + 1] - limits[j])
            red = (1-coeff) * self.colors[j][0] + coeff * self.colors[j + 1][0]
            green = (1-coeff) * self.colors[j][1] + coeff * self.colors[j +
                                                                        1][1]
            blue = (1-coeff) * self.colors[j][2] + coeff * self.colors[j + 1][2]

            self.table.append(
                QColor(red * color_max, green * color_max,
                       blue * color_max).rgba())

        if self.saturation_high_color is not None:
            self.table.append(
                QColor(self.saturation_high_color[0] * color_max,
                       self.saturation_high_color[1] * color_max,
                       self.saturation_high_color[2] * color_max).rgba())

        if self.has_transparency:
            self.table.append(QColor(0, 0, 0, 0).rgba())


class ColormapCSV(Colormap):
    file = None
    scale = 1

    def __init__(self):
        cmap = pd.read_csv(self.file)

        self.table = []
        for i, row in cmap.iterrows():
            self.table.append(
                QColor(row['RGB_r'] * self.scale, row['RGB_g'] * self.scale,
                       row['RGB_b'] * self.scale).rgba())

        if self.has_transparency:
            self.transparency_value = self.max
            self.max -= 1
            self.table[-1] = QColor(0, 0, 0, 0).rgba()


class Grayscale(ColormapExtrapolated):
    colors = [(0, 0, 0), (1, 1, 1)]


class GrayscaleSaturation(ColormapExtrapolated):
    colors = [(0, 0, 0), (1, 1, 1)]
    saturation_low_color = (0, 0, 1)
    saturation_high_color = (1, 0, 0)


class GrayscaleTransparent(ColormapExtrapolated):
    colors = [(0, 0, 0), (1, 1, 1)]
    has_transparency = True


class GrayscaleSaturationTransparent(ColormapExtrapolated):
    colors = [(0, 0, 0), (1, 1, 1)]
    saturation_low_color = (0, 0, 1)
    saturation_high_color = (1, 0, 0)
    has_transparency = True


class CoolWarm(ColormapCSV):
    file = colormaps_path / 'smooth-cool-warm-table-byte-0256.csv'
    no_data_value = 128


class BlackBody(ColormapCSV):
    file = colormaps_path / 'black-body-table-byte-0256.csv'


class Inferno(ColormapCSV):
    file = colormaps_path / 'inferno-table-byte-0256.csv'


class Plasma(ColormapCSV):
    file = colormaps_path / 'plasma-table-byte-0256.csv'


class Kindlmann(ColormapCSV):
    file = colormaps_path / 'kindlmann-table-byte-0256.csv'


class Viridis(ColormapCSV):
    file = colormaps_path / 'viridis-table-byte-0256.csv'


class CoolWarmTransparent(ColormapCSV):
    file = colormaps_path / 'smooth-cool-warm-table-byte-0256.csv'
    no_data_value = 128

    has_transparency = True


class BlackBodyTransparent(ColormapCSV):
    file = colormaps_path / 'black-body-table-byte-0256.csv'

    has_transparency = True


class ColormapLabel(QLabel):
    def scaledPixmap(self):
        return self.pixmap().scaled(self.size(), Qt.IgnoreAspectRatio,
                                    Qt.FastTransformation)

    def resizeEvent(self, e):
        super().setPixmap(self.scaledPixmap())


def show_colormap(colormap):
    if not hasattr(show_colormap, 'pos_y'):
        show_colormap.pos_y = 100
        show_colormap.labels = []

    label = ColormapLabel()
    label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    array = np.arange(0, 256).reshape(1, 256)
    img_uint8 = np.require(array, np.uint8, 'C')
    image = QImage(img_uint8.data, img_uint8.shape[1], img_uint8.shape[0],
                   img_uint8.shape[1], QImage.Format_Indexed8)
    image.setColorTable(colormap.table)

    pixmap = QPixmap.fromImage(image)
    label.setPixmap(pixmap)

    show_colormap.labels.append(label)

    label.setWindowTitle(colormap.__class__.__name__)
    label.resize(1024, 50)

    label.show()

    label.move(
        label.screen().geometry().center().x() - label.rect().center().x(),
        show_colormap.pos_y)

    show_colormap.pos_y += label.size().height() + QApplication.style(
    ).pixelMetric(QStyle.PM_TitleBarHeight)


def get_all_colormaps(exclude_transparent=False):
    colormaps = []

    for name, obj in inspect.getmembers(sys.modules[__name__],
                                        inspect.isclass):
        if issubclass(obj, Colormap):
            if name in ['Colormap', 'ColormapCSV', 'ColormapExtrapolated']:
                continue
            elif exclude_transparent and obj.has_transparency:
                continue

            colormaps.append(obj)

    return colormaps


if __name__ == '__main__':
    app = QApplication(['KalAO - Colormaps'])
    app.setQuitOnLastWindowClosed(True)

    for obj in get_all_colormaps():
        show_colormap(obj())

    app.exec()
