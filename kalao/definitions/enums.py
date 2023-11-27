# From python 3.11
#from enum import StrEnum

# Emulate StrEnum for python < 3.11
from enum import Enum, Flag, IntEnum, IntFlag, auto


class StrEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class LogsOutputType(StrEnum):
    RAW = 'RAW'
    TEXT = 'TEXT'
    HTML = 'HTML'


class ServiceAction(StrEnum):
    RESTART = 'RESTART'
    START = 'START'
    STOP = 'STOP'
    RELOAD = 'RELOAD'
    KILL = 'KILL'
    DISABLE = 'DISABLE'
    ENABLE = 'ENABLE'
    STATUS = 'STATUS'


class LoopStatus(Flag):
    DM_LOOP_ON = auto()
    TTM_LOOP_ON = auto()
    ERROR = auto()

    ALL_LOOPS_OFF = 0
    ALL_LOOPS_ON = DM_LOOP_ON | TTM_LOOP_ON


class TrackingStatus(StrEnum):
    IDLE = 'IDLE'
    POINTING = 'POINTING'
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
    ABORTING = 'ABORTING'
    OFF = 'OFF'


class IPPowerStatus(IntEnum):
    OFF = 0
    ON = 1
    ERROR = -1


class CameraServerStatus(StrEnum):
    UP = 'UP'
    DOWN = 'DOWN'
    ERROR = 'ERROR'


class FlipMirrorPosition(StrEnum):
    UP = 'UP'
    DOWN = 'DOWN'
    ERROR = 'ERROR'


class ShutterState(StrEnum):
    OPEN = 'OPEN'
    CLOSED = 'CLOSED'
    ERROR = 'ERROR'


class FilterwheelStatus(Enum):
    ERROR_POSITION = -1
    ERROR_NAME = 'error'


class TungstenStatus:
    ON = 'ON'
    OFF = 'OFF'


class ReturnCode(IntFlag):
    @staticmethod
    def _generate_next_value_(name, start, count, last_values):
        cur = min(last_values)
        high_bit = cur.bit_length() - 1
        return -1 * 2**(high_bit + 1)

    NOERROR = 0
    GENERIC_ERROR = -1

    SEQ_OK = NOERROR

    CENTERING_OK = NOERROR

    CAMERA_OK = NOERROR
    CAMERA_SERVER_DOWN = auto()
    CAMERA_ERROR = auto()

    DM_ON_FAILED = auto()

    TRACKING_TIMEOUT = auto()
