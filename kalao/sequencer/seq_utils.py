import time

from kalao import database, logger, memory

from kalao.definitions.enums import SequencerStatus
from kalao.definitions.exceptions import AbortRequested

_transitions = {
    SequencerStatus.UNKNOWN: [SequencerStatus.INITIALISING],
    SequencerStatus.OFF: [SequencerStatus.INITIALISING],
    SequencerStatus.INITIALISING: [SequencerStatus.WAITING],
    SequencerStatus.WAITING: [SequencerStatus.SETUP],
    SequencerStatus.SETUP: [
        SequencerStatus.EXPOSING, SequencerStatus.FOCUSING,
        SequencerStatus.CENTERING, SequencerStatus.WAIT_TRACKING,
        SequencerStatus.WAITING, SequencerStatus.ERROR
    ],
    SequencerStatus.FOCUSING: [SequencerStatus.WAITING, SequencerStatus.ERROR],
    SequencerStatus.EXPOSING: [SequencerStatus.WAITING, SequencerStatus.ERROR],
    SequencerStatus.CENTERING: [SequencerStatus.SETUP],
    SequencerStatus.WAIT_TRACKING: [SequencerStatus.SETUP],
    SequencerStatus.WAIT_LAMP: [SequencerStatus.SETUP],
    SequencerStatus.ERROR: [SequencerStatus.SETUP],
    SequencerStatus.ABORTING: [SequencerStatus.WAITING, SequencerStatus.OFF],
    SequencerStatus.ABORTING_ERROR: [SequencerStatus.ERROR],
}


def get_sequencer_status() -> SequencerStatus:
    return SequencerStatus(
        memory.hget('sequencer', 'status', default=SequencerStatus.UNKNOWN))


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
        memory.hmset('sequencer', {
            'status': status,
            'status_timestamp': time.time()
        })
    else:
        memory.hset('sequencer', 'status', status)
    database.store('obs', {'sequencer_status': status})


def is_aborting() -> bool:
    status = get_sequencer_status()
    return status in [SequencerStatus.ABORTING, SequencerStatus.ABORTING_ERROR]


class SequencerStatusContextManager:
    def __init__(self, status):
        self.status = status

    def __enter__(self):
        self.previous_status = get_sequencer_status()
        _set_sequencer_status(self.status, update_timestamp=False)

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore previous status if status didn't change
        # (e.g. do not change if status was switched to ABORTING or ERROR)
        if get_sequencer_status() == self.status:
            _set_sequencer_status(self.previous_status, update_timestamp=False)
