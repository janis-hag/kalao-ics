from dataclasses import dataclass, field

import numpy as np


@dataclass
class ROI:
    x: int
    y: int
    width: int
    height: int


@dataclass
class Star:
    x: float
    y: float
    peak: float
    fwhm_w: float
    fwhm_h: float
    fwhm_angle: float

    fwhm: float = field(init=False)

    def __post_init__(self):
        self.fwhm = np.sqrt(self.fwhm_w * self.fwhm_h)