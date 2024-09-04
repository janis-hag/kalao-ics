from dataclasses import dataclass, field
from datetime import datetime

import numpy as np

from kalao.common.enums import AlarmLevel, LogLevel, TemplateID

from kalao.ics import memory


@dataclass
class ObservationBlock:
    tplno: int = 0


@dataclass
class Template:
    id: TemplateID
    start: datetime | None
    observation_block: ObservationBlock | None = None
    nexp: int = -1
    expno: int = 0

    def to_memory(self):
        memory.hmset(
            'sequencer', {
                'id': self.id,
                'start': self.start.timestamp(),
                'nexp': self.nexp,
                'expno': self.expno
            })

    def next_exposure(self):
        self.expno += 1
        memory.hset('sequencer', 'expno', self.expno)


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
    cursor: str
    level: LogLevel
    timestamp: datetime
    origin: str
    message: str


@dataclass
class CalibrationPose:
    template: Template
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
