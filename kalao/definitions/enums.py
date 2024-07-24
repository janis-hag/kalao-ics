from enum import Flag, IntEnum, StrEnum, auto


class ObservationType(StrEnum):
    TARGET = 'K_TRGOBS'
    BIAS = 'K_BIAS'
    DARK = 'K_DARK'
    SKY_FLAT = 'K_SKYFLT'
    LAMP_FLAT = 'K_LMPFLT'
    FOCUS = 'K_FOCUS'
    TARGET_CENTERING = 'K_TRGCEN'
    LASER_CENTERING = 'K_LSRCEN'
    ENGINEERING = 'K_ENGIN'


class CenteringMode(StrEnum):
    MANUAL = 'man'
    AUTOMATIC = 'auto'
    NONE = 'no'


class AdaptiveOpticsMode(StrEnum):
    ENABLED = 'AO'
    DISABLED = 'NO_AO'


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
    ALL_LOOPS_OFF = 0

    DM_LOOP_ON = auto()
    TTM_LOOP_ON = auto()
    ERROR = auto()

    ALL_LOOPS_ON = DM_LOOP_ON | TTM_LOOP_ON


class SequencerStatus(StrEnum):
    ERROR = 'ERROR'
    UNKNOWN = 'ERROR'
    OFF = 'OFF'
    INITIALISING = 'INITIALISING'
    WAITING = 'WAITING'
    BUSY = 'BUSY'
    SETUP = 'SETUP'
    CENTERING = 'CENTERING'
    FOCUSING = 'FOCUSING'
    EXPOSING = 'EXPOSING'
    CALIBRATIONS = 'CALIBRATIONS'
    WAIT_LAMP = 'WAIT_LAMP'
    WAIT_TRACKING = 'WAIT_TRACKING'
    ABORTING = 'ABORTING'
    ABORTING_ERROR = 'ABORTING_ERROR'


class IPPowerStatus(IntEnum):
    OFF = 0
    ON = 1
    ERROR = -1


class CameraServerStatus(StrEnum):
    UP = 'UP'
    DOWN = 'DOWN'
    ERROR = 'ERROR'


class ETCSServerStatus(StrEnum):
    UP = 'UP'
    DOWN = 'DOWN'
    ERROR = 'ERROR'


class CameraStatus(StrEnum):
    UNKNOWN = 'unknown'
    IDLE = 'idle'
    WAITING_TRIGGER = 'waiting-trigger'
    EXPOSING = 'exposing'
    READING_CCD = 'reading-ccd'
    ERROR = 'error'


class CalibUnitPositionName(StrEnum):
    UNKNOWN = 'Unknown'
    LASER = 'Laser'
    TUNGSTEN = 'Tungsten'
    ERROR = 'Error'


class FlipMirrorStatus(StrEnum):
    UP = 'UP'
    DOWN = 'DOWN'
    UNKNOWN = 'UNKNOWN'
    ERROR = 'ERROR'


class ShutterStatus(StrEnum):
    OPEN = 'OPEN'
    CLOSED = 'CLOSED'
    ERROR = 'ERROR'


class FilterWheelStatus:
    ERROR_POSITION = -1
    ERROR_NAME = 'error'


class TungstenStatus(StrEnum):
    ON = 'ON'
    OFF = 'OFF'
    ERROR = 'ERROR'


class LaserStatus(StrEnum):
    ON = 'ON'
    OFF = 'OFF'
    ERROR = 'ERROR'


class RelayState(StrEnum):
    ON = 'ON'
    OFF = 'OFF'
    ERROR = 'ERROR'


class PLCStatus(StrEnum):
    NOT_ENABLED = 'NOT_ENABLED'
    INITIALISING = 'INITIALISING'
    NOT_INITIALISED = 'NOT_INITIALISED'
    ERROR = 'ERROR'
    MOVING = 'MOVING'
    STANDING = 'STANDING'
    UNKNOWN = 'UNKNOWN'


class ReturnCode(IntEnum):
    # TODO: This is fixed in python 3.13
    def _generate_next_value_(name, start, count, last_values):
        if not last_values:
            return start
        else:
            return max(last_values) + 1

    OK = 0
    GENERIC_ERROR = -1
    TIMEOUT = -2
    EXCEPTION = -3

    SEQ_OK = OK
    SEQ_ERROR = auto()

    FOCUSING_OK = OK
    FOCUSING_ERROR = auto()

    CENTERING_OK = OK
    CENTERING_TIMEOUT = auto()
    CENTERING_ERROR = auto()

    CAMERA_OK = OK
    CAMERA_SERVER_DOWN = auto()
    CAMERA_ERROR = auto()

    ETCS_OK = OK
    ETCS_SERVER_DOWN = auto()
    ETCS_ERROR = auto()

    HW_INIT_SUCCESS = OK
    HW_INIT_FAILED = auto()

    DATABASE_OK = OK
    DATABASE_ERROR = auto()

    IPPOWER_OK = OK
    IPPOWER_ERROR = auto()

    SERVICES_OK = OK
    SERVICES_ERROR = auto()


class AlarmLevel(StrEnum):
    ALARM = 'ALARM'
    WARNING = 'WARNING'
    OK = 'OK'


class ReportType(StrEnum):
    CLI = 'CLI'
    HTML = 'HTML'
