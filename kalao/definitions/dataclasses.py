from dataclasses import dataclass, field
from datetime import datetime

import numpy as np

from kalao.definitions.enums import LogLevel


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


@dataclass
class LogEntry:
    level: LogLevel
    timestamp: datetime
    origin: str
    message: str
