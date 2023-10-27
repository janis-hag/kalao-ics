# From python 3.11
#from enum import StrEnum

# Emulate StrEnum for python < 3.11
from enum import Enum, IntEnum


class StrEnum(str, Enum):

    def __str__(self) -> str:
        return self.value


class TrackingStatus(StrEnum):
    IDLE = 'IDLE'
    CENTERING = 'CENTERING'
    TRACKING = 'TRACKING'


class SequencerStatus(StrEnum):
    ERROR = 'ERROR'
    INITIALISING = 'INITIALISING'
    SETUP = 'SETUP'
    WAITING = 'WAITING'
    WAITLAMP = 'WAITLAMP'
    BUSY = 'BUSY'
    EXP = 'EXP'


class IPPowerStatus(IntEnum):
    ON = 1
    OFF = 0
