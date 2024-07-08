import numpy as np


def cut(img: np.ndarray, window: tuple[int, int] | int,
        center: tuple[int, int] | None = None,
        overflow: str = 'recenter') -> np.ndarray:
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
    __name__ = 'Abstract'

    def __init__(self, min: float = 0, max: float = 255) -> None:
        self.min = min
        self.max = max
        self.delta = self.max - self.min

    def __str__(self) -> str:
        return self.__name__


class LinearScale(AbstractScale):
    __name__ = 'Linear'

    def scale(self, img: np.ndarray) -> np.ndarray:
        return img

    def inverse(self, img: np.ndarray) -> np.ndarray:
        return img


class LogScale(AbstractScale):
    __name__ = 'Logarithmic'

    def scale(self, img: np.ndarray) -> np.ndarray:
        return self.delta / np.log(self.delta + 1) * np.log(img - self.min +
                                                            1) + self.min

    def inverse(self, img: np.ndarray) -> np.ndarray:
        return np.exp(np.log(self.delta + 1) / self.delta *
                      (img - self.min)) + self.min - 1


class SquareRootScale(AbstractScale):
    __name__ = 'Square Root'

    def scale(self, img: np.ndarray) -> np.ndarray:
        return np.sqrt(self.delta) * np.sqrt(img - self.min) + self.min

    def inverse(self, img: np.ndarray) -> np.ndarray:
        return ((img - self.min) / np.sqrt(self.delta))**2 + self.min


class SquaredScale(AbstractScale):
    __name__ = 'Squared'

    def scale(self, img: np.ndarray) -> np.ndarray:
        return (img - self.min)**2 / self.delta + self.min

    def inverse(self, img: np.ndarray) -> np.ndarray:
        return np.sqrt(self.delta * (img - self.min)) + self.min


### Cuts


class AbstractCut():
    def __init__(self) -> None:
        pass

    def cut(self, img: np.ndarray) -> tuple[float, float]:
        return img.min(), img.max()

    def img_cut(self, img):
        low, high = self.cut(img)

        img = np.where(img < low, low, img)
        img = np.where(img > high, high, img)

        return img


class MinMaxCut(AbstractCut):
    def __init__(self) -> None:
        super().__init__()

    def __str__(self) -> str:
        return 'Min – Max'

    def cut(self, img: np.ndarray) -> tuple[float, float]:
        return img.min(), img.max()


class PercentileCut(AbstractCut):
    def __init__(self, percentile: float = 0.1) -> None:
        super().__init__()

        self.percentile = percentile

    def __str__(self) -> str:
        return f'Percentile, {self.percentile:g}% – {100-self.percentile:g}%'

    def cut(self, img: np.ndarray) -> tuple[float, float]:
        return np.percentile(img, self.percentile), np.percentile(
            img, 100 - self.percentile)


class SigmaCut(AbstractCut):
    def __init__(self, sigma: float = 3) -> None:
        super().__init__()

        self.sigma = sigma

    def __str__(self) -> str:
        return f'Sigma, {-self.sigma:g}σ – {self.sigma:g}σ'

    def cut(self, img: np.ndarray) -> tuple[float, float]:
        mean = img.mean()
        std = img.std()

        return mean - self.sigma * std, mean + self.sigma * std
