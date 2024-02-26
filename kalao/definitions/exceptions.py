class SequencerException(Exception):
    """Generic sequencer error."""


class AbortRequested(SequencerException):
    """An abort was requested."""


class MissingKeyword(SequencerException):
    """Missing keyword in function call."""


class LoopNotClosed(SequencerException):
    """Failed to close loops"""


class LoopsNotOpen(SequencerException):
    """Failed to open loops"""


class EMGainNotOff(SequencerException):
    """Failed to disable EM gain on WFS"""


class DMNotOn(SequencerException):
    """Failed to power on DM driver"""


class WFSNotOn(SequencerException):
    """Failed to start WFS acquisition"""


class DMResetFailed(SequencerException):
    """Failed to reset DMs"""


class ShutterNotOpen(SequencerException):
    """Shutter did not open"""


class ShutterNotClosed(SequencerException):
    """Shutter did not close"""


class FlipMirrorNotUp(SequencerException):
    """Flip mirror did not go up"""


class FlipMirrorNotDown(SequencerException):
    """Flip mirror did not go down"""


class FilterWheelNotInPosition(SequencerException):
    """Wrong filter selected in filter wheel"""


class TungstenNotOn(SequencerException):
    """Tungsten lamp did not switch on"""


class TungstenNotInPosition(SequencerException):
    """Tungsten lamp not in position"""


class TungstenSwitchedOff(SequencerException):
    """Tungsten lamp unexpectedly switched off"""


class LampsNotOff(SequencerException):
    """Lamps did not turn off"""


class TrackingTimeout(SequencerException):
    """Tracking timeout"""


class FLITakeImageFailed(SequencerException):
    """Failed to take image"""


class FLICancelFailed(SequencerException):
    """Failed to cancel camera exposure"""


class ADCConfigureFailed(SequencerException):
    """Failed to configure ADC"""


class CenteringFailed(SequencerException):
    """Failed to center on target"""


class FocusSequenceFailed(SequencerException):
    """Focus sequence failed"""


##### Centering


class CenteringException(SequencerException):
    """Generic centering error."""


class ManualCenteringTimeout(CenteringException):
    """Timeout during manual centering"""


class AutomaticCenteringTimeout(CenteringException):
    """Timeout during automatic centering"""


class CenteringMaxIter(CenteringException):
    """Maximum iterations reached during centering"""


class CenteringStarNotFound(CenteringException):
    """Star not found"""


class CenteringFluxWFSTooLow(CenteringException):
    """Flux on WFS is too low"""


class CenteringOffsetingFailed(CenteringException):
    """Offsetting to telescope failed"""


##### Focusing


class FocusingException(SequencerException):
    """Generic focusing error."""


class FocusingAbortRequested(FocusingException):
    """Abort requested"""


class FocusingTakeImageFailed(FocusingException):
    """Camera returned no image"""


class FocusingStarNotFound(FocusingException):
    """Star not found"""


class FocusingInvertedCurve(FocusingException):
    """Inverted curve"""


class FocusingMinimaOutsideRange(FocusingException):
    """Minima outside focusing range"""


class FocusingNoMinima(FocusingException):
    """No minima reached"""


class FocusingSaturated(FocusingException):
    """Image saturated, can't estimate FWHM"""
