from PySide2.QtGui import QColor


class Colormap:
    colormap = None

    colors = None
    color_saturation_low = None
    color_saturation_high = None
    has_transparency = False

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


class BWR(Colormap):
    colors = [(0, 0, 1), (1, 1, 1), (1, 0, 0)]


class Grayscale(Colormap):
    colors = [(0, 0, 0), (1, 1, 1)]


class Hot(Colormap):
    colors = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (1, 1, 1)]


class GrayscaleSaturation(Colormap):
    colors = [(0, 0, 0), (1, 1, 1)]
    color_saturation_low = (0, 0, 1)
    color_saturation_high = (1, 0, 0)
