from enum import StrEnum


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
