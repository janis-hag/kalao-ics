# From python 3.11
#from enum import StrEnum

# Emulate StrEnum for python < 3.11
from enum import Enum, Flag, IntEnum, auto


class StrEnum(str, Enum):

    def __str__(self) -> str:
        return self.value


class LoopStatus(Flag):
    DM_LOOP_ON = auto()
    TTM_LOOP_ON = auto()

    ALL_LOOPS_ON = DM_LOOP_ON & TTM_LOOP_ON


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
    OFF = 0
    ON = 1


class CameraServerStatus(StrEnum):
    UP = 'UP'
    DOWN = 'DOWN'
    ERROR = 'ERROR'