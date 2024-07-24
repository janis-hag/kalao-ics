from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable

from kalao import database, logger, memory

from kalao.definitions.enums import SequencerStatus
from kalao.definitions.exceptions import AbortRequested

_transitions = {
    SequencerStatus.UNKNOWN: [SequencerStatus.INITIALISING],
    SequencerStatus.OFF: [SequencerStatus.INITIALISING],
    SequencerStatus.INITIALISING: [SequencerStatus.WAITING],
    SequencerStatus.WAITING: [SequencerStatus.BUSY],
    SequencerStatus.BUSY: [SequencerStatus.SETUP],
    SequencerStatus.SETUP: [
        SequencerStatus.EXPOSING, SequencerStatus.FOCUSING,
        SequencerStatus.CENTERING, SequencerStatus.CALIBRATIONS,
        SequencerStatus.WAIT_TRACKING, SequencerStatus.WAITING,
        SequencerStatus.ERROR
    ],
    SequencerStatus.FOCUSING: [SequencerStatus.WAITING, SequencerStatus.ERROR],
    SequencerStatus.EXPOSING: [SequencerStatus.WAITING, SequencerStatus.ERROR],
    SequencerStatus.CALIBRATIONS: [
        SequencerStatus.WAITING, SequencerStatus.ERROR
    ],
    SequencerStatus.CENTERING: [SequencerStatus.SETUP],
    SequencerStatus.WAIT_TRACKING: [SequencerStatus.SETUP],
    SequencerStatus.WAIT_LAMP: [SequencerStatus.CALIBRATIONS],
    SequencerStatus.ERROR: [SequencerStatus.BUSY],
}


def get_sequencer_status() -> SequencerStatus:
    return SequencerStatus(
        memory.get('sequencer_status', default=SequencerStatus.UNKNOWN))


def set_sequencer_status(status: SequencerStatus, check_abort=False) -> None:
    current_status = get_sequencer_status()

    if status not in _transitions[current_status] + [
            SequencerStatus.ABORTING, SequencerStatus.ABORTING_ERROR
    ]:
        logger.error(
            'sequencer',
            f'Forbidden transition from {current_status} to {status}')

    if check_abort and current_status in [
            SequencerStatus.ABORTING, SequencerStatus.ABORTING_ERROR
    ]:
        raise AbortRequested

    return _set_sequencer_status(status)


def _set_sequencer_status(status: SequencerStatus,
                          update_timestamp=True) -> None:
    if update_timestamp:
        memory.mset({
            'sequencer_status':
                str(status),
            'sequencer_status_timestamp':
                datetime.now(timezone.utc).timestamp()
        })
    else:
        memory.set('sequencer_status', str(status))
    database.store('obs', {'sequencer_status': status})


def is_aborting() -> bool:
    status = get_sequencer_status()
    return status in [SequencerStatus.ABORTING, SequencerStatus.ABORTING_ERROR]


def with_sequencer_status(status: SequencerStatus) -> Any:
    def _with_sequencer_status(fun: Callable) -> Any:
        @wraps(fun)
        def wrapper(*args: tuple[Any, ...], **kwargs: dict[str, Any]) -> Any:
            ret = None
            exception = None

            previous_status = get_sequencer_status()
            _set_sequencer_status(status, update_timestamp=False)

            try:
                ret = fun(*args, **kwargs)
            except Exception as e:
                exception = e

            current_status = get_sequencer_status()

            # Restore previous status if status didn't change
            # (e.g. do not change if status was switched to ABORTING or ERROR)
            if current_status == status:
                _set_sequencer_status(previous_status, update_timestamp=False)

            if exception is not None:
                raise exception

            return ret

        return wrapper

    return _with_sequencer_status
