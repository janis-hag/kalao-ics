from pathlib import Path

import numpy as np
import pandas as pd

from PySide2.QtGui import QColor, QImage, QPixmap
from PySide2.QtWidgets import QApplication, QLabel

colormap_path = Path(__file__).absolute().parent.parent / 'colormaps'

# See https://www.kennethmoreland.com/color-advice/


class Colormap:
    colormap = None

    color_saturation_low = None
    color_saturation_high = None
    has_transparency = False


class ColormapExtrapolated(Colormap):
    colors = None

    def __init__(self, start=0, end=255, color_max=255):
        length = len(self.colors)

        if self.color_saturation_low is not None:
            start += 1

        if self.color_saturation_high is not None:
            end -= 1

        if self.has_transparency:
            end -= 1

        limits = []
        for i in range(length):
            limits.append(start + i * (end-start) / (length-1))

        self.colormap = []
        j = 0

        if self.color_saturation_low is not None:
            self.colormap.append(
                QColor(self.color_saturation_low[0] * color_max,
                       self.color_saturation_low[1] * color_max,
                       self.color_saturation_low[2] * color_max).rgba())

        for i in range(start, end + 1):
            if i > limits[j + 1]:
                j += 1

            coeff = (i - limits[j]) / (limits[j + 1] - limits[j])
            red = (1-coeff) * self.colors[j][0] + coeff * self.colors[j + 1][0]
            green = (1-coeff) * self.colors[j][1] + coeff * self.colors[j +
                                                                        1][1]
            blue = (1-coeff) * self.colors[j][2] + coeff * self.colors[j + 1][2]

            #print(i, red* color_max, green* color_max, blue* color_max)

            self.colormap.append(
                QColor(red * color_max, green * color_max,
                       blue * color_max).rgba())

        if self.color_saturation_high is not None:
            self.colormap.append(
                QColor(self.color_saturation_high[0] * color_max,
                       self.color_saturation_high[1] * color_max,
                       self.color_saturation_high[2] * color_max).rgba())

        if self.has_transparency is not None:
            self.colormap.append(QColor(0, 0, 0, 0).rgba())


class ColormapCSV(Colormap):
    file = None
    scale = 1

    def __init__(self):
        cmap = pd.read_csv(self.file)

        self.colormap = []
        for i, row in cmap.iterrows():
            self.colormap.append(
                QColor(row['RGB_r'] * self.scale, row['RGB_g'] * self.scale,
                       row['RGB_b'] * self.scale).rgba())


class BWR(ColormapExtrapolated):
    colors = [(0, 0, 1), (1, 1, 1), (1, 0, 0)]


class Grayscale(ColormapExtrapolated):
    colors = [(0, 0, 0), (1, 1, 1)]


class Hot(ColormapExtrapolated):
    colors = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (1, 1, 1)]


class GrayscaleSaturation(ColormapExtrapolated):
    colors = [(0, 0, 0), (1, 1, 1)]
    color_saturation_low = (0, 0, 1)
    color_saturation_high = (1, 0, 0)


class CoolWarm(ColormapCSV):
    file = colormap_path / 'smooth-cool-warm-table-byte-0256.csv'


class BlackBody(ColormapCSV):
    file = colormap_path / 'black-body-table-byte-0256.csv'


class Inferno(ColormapCSV):
    file = colormap_path / 'inferno-table-byte-0256.csv'


def show_colormap(colormap):
    label = QLabel()

    array = np.arange(0, 256).reshape(1, 256)
    img_uint8 = np.require(array, np.uint8, 'C')
    image = QImage(img_uint8.data, img_uint8.shape[1], img_uint8.shape[0],
                   img_uint8.shape[1], QImage.Format_Indexed8)
    image.setColorTable(colormap.colormap)

    pixmap = QPixmap.fromImage(image).scaled(1024, 50)
    label.setPixmap(pixmap)

    labels.append(label)

    label.setWindowTitle(colormap.__class__.__name__)

    label.show()


if __name__ == "__main__":
    app = QApplication(['KalAO - Colormaps'])
    app.setQuitOnLastWindowClosed(True)

    labels = []

    show_colormap(GrayscaleSaturation())
    show_colormap(Grayscale())
    show_colormap(BWR())
    show_colormap(Hot())
    show_colormap(CoolWarm())
    show_colormap(BlackBody())
    show_colormap(Inferno())

    app.exec_()
