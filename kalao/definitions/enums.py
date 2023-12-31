# From python 3.11
#from enum import StrEnum

# Emulate StrEnum for python < 3.11
from enum import Enum, Flag, IntEnum, IntFlag, auto


class StrEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class LogsOutputType(StrEnum):
    RAW = 'RAW'
    JSON = 'JSON'


class LogLevel(StrEnum):
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'


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


class T120ServerStatus(StrEnum):
    UP = 'UP'
    DOWN = 'DOWN'
    ERROR = 'ERROR'


class FlipMirrorPosition(StrEnum):
    UP = 'UP'
    DOWN = 'DOWN'
    UNKNOWN = 'UNKNOWN'
    ERROR = 'ERROR'


class ShutterState(StrEnum):
    OPEN = 'OPEN'
    CLOSED = 'CLOSED'
    ERROR = 'ERROR'


class FilterwheelStatus(Enum):
    ERROR_POSITION = -1
    ERROR_NAME = 'error'


class TungstenState(StrEnum):
    ON = 'ON'
    OFF = 'OFF'
    ERROR = 'ERROR'


class LaserState(StrEnum):
    ON = 'ON'
    OFF = 'OFF'
    ERROR = 'ERROR'


class RelayState(StrEnum):
    ON = 'ON'
    OFF = 'OFF'
    ERROR = 'ERROR'


class PLCStatus(StrEnum):
    DISABLED = 'DISABLED'
    INITIALISING = 'INITIALISING'
    UNINITIALISED = 'UNINITIALISED'
    ERROR = 'ERROR'
    MOVING = 'MOVING'
    STANDING = 'STANDING'
    UNKNOWN = 'UNKNOWN'


class ReturnCode(IntFlag):
    OK = 0
    GENERIC_ERROR = -1
    TIMEOUT = -2

    SEQ_OK = OK

    CENTERING_OK = OK
    CENTERING_TIMEOUT = auto()

    CAMERA_OK = OK
    CAMERA_SERVER_DOWN = auto()
    CAMERA_ERROR = auto()

    T120_OK = OK
    T120_SERVER_DOWN = auto()
    T120_ERROR = auto()

    PLC_INIT_SUCCESS = OK
    PLC_INIT_FAILED = auto()
