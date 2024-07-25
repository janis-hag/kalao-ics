from dataclasses import dataclass, field
from datetime import datetime

import numpy as np

from kalao.definitions.enums import AlarmLevel, LogLevel, ObservationType


@dataclass(frozen=True)
class ROI:
    x: int
    y: int
    width: int
    height: int


@dataclass(frozen=True)
class Star:
    x: float
    y: float
    peak: float
    fwhm_w: float
    fwhm_h: float
    fwhm_angle: float

    fwhm: float = field(init=False)

    def __post_init__(self):
        object.__setattr__(self, 'fwhm', np.sqrt(self.fwhm_w * self.fwhm_h))


@dataclass(frozen=True)
class LogEntry:
    level: LogLevel
    timestamp: datetime
    origin: str
    message: str


@dataclass
class CalibrationPose:
    type: ObservationType
    filter: str | None
    exposure_time: float
    median: float = np.nan
    status: str = 'IDLE'
    error_text: str = ''


@dataclass(frozen=True)
class Alarm:
    level: AlarmLevel
    condition: str
    threshold: float
