import numpy as np


def cut(img, window, center=None, overflow='recenter'):
    if isinstance(window, int):
        hw = window // 2
        hh = window // 2
    else:
        hw = window[0] // 2
        hh = window[1] // 2

    if center is None:
        cx, cy = [img.shape[1] // 2, img.shape[0] // 2]
    else:
        cx, cy = center

    if overflow == 'recenter':
        if cx + hw > img.shape[1]:
            cx = img.shape[1] - hw
        elif cx - hw < 0:
            cx = hw

        if cy + hh > img.shape[0]:
            cy = img.shape[0] - hh
        elif cy - hh < 0:
            cy = hh

    xs = cx - hw
    xe = cx + hw
    ys = cy - hh
    ye = cy + hh

    if xs < 0:
        xs = 0
    if xe > img.shape[1]:
        xe = img.shape[1]
    if ys < 0:
        ys = 0
    if ye > img.shape[0]:
        ye = img.shape[0]

    return img[ys:ye, xs:xe]


### Scales


class AbstractScale():
    def __init__(self, min=0, max=255):
        self.min = min
        self.max = max
        self.delta = self.max - self.min


class LinearScale(AbstractScale):
    __name__ = 'Linear'

    def __str__(self):
        return self.__name__

    def scale(self, img):
        return img


class LogScale(AbstractScale):
    __name__ = 'Logarithmic'

    def __str__(self):
        return self.__name__

    def scale(self, img):
        return self.delta / np.log(self.delta + 1) * np.log(img - self.min +
                                                            1) + self.min


class SquareRootScale(AbstractScale):
    __name__ = 'Square Root'

    def __str__(self):
        return self.__name__

    def scale(self, img):
        return np.sqrt(self.delta) * np.sqrt(img - self.min) + self.min


class SquaredScale(AbstractScale):
    __name__ = 'Squared'

    def __str__(self):
        return self.__name__

    def scale(self, img):
        return 1 / self.delta * (img - self.min)**2 + self.min


### Cuts


class AbstractCut():
    def __init__(self):
        pass

    def img_cut(self, img):
        low, high = self.cuts(self, img)

        img = np.where(img < low, low, img)
        img = np.where(img > high, high, img)

        return img


class MinMaxCut():
    def __init__(self):
        pass

    def __str__(self):
        return 'Min – Max'

    def cut(self, img):
        return img.min(), img.max()


class PercentileCut():
    def __init__(self, percentile=0.1):
        self.percentile = percentile

    def __str__(self):
        return f'Percentile, {self.percentile:g}% – {100-self.percentile:g}%'

    def cut(self, img):
        return np.percentile(img, self.percentile), np.percentile(
            img, 100 - self.percentile)


class SigmaCut():
    def __init__(self, sigma=3):
        self.sigma = sigma

    def __str__(self):
        return f'Sigma, {-self.sigma:g}σ – {self.sigma:g}σ'

    def cut(self, img):
        mean = img.mean()
        std = img.std()

        return mean - self.sigma * std, mean + self.sigma * std
