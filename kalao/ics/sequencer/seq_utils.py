import time

from kalao.common.enums import SequencerStatus, WindowHint
from kalao.common.exceptions import AbortRequested

from kalao.ics import database, logger, memory

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
    SequencerStatus.ABORTING_USER: [
        SequencerStatus.WAITING, SequencerStatus.OFF
    ],
    SequencerStatus.ABORTING_SOFTWARE: [SequencerStatus.ERROR],
}


def get_sequencer_status() -> SequencerStatus:
    return SequencerStatus(
        memory.hget('sequencer', 'status', default=SequencerStatus.UNKNOWN))


def set_sequencer_status(status: SequencerStatus, check_abort=False,
                         check_status=False) -> None:
    current_status = get_sequencer_status()

    if status not in _transitions[current_status] + [
            SequencerStatus.ABORTING_USER, SequencerStatus.ABORTING_SOFTWARE
    ]:
        logger.error(
            'sequencer',
            f'Forbidden transition from {current_status} to {status}')

    if check_abort and current_status in [
            SequencerStatus.ABORTING_USER, SequencerStatus.ABORTING_SOFTWARE
    ]:
        raise AbortRequested

    return _set_sequencer_status(status, check_status=check_status)


def _set_sequencer_status(status: SequencerStatus, update_timestamp=True,
                          check_status=False) -> None:
    if check_status and get_sequencer_status() == status:
        # Status already OK, skipping
        return

    if update_timestamp:
        memory.hmset('sequencer', {
            'status': status,
            'status_timestamp': time.time()
        })
    else:
        memory.hset('sequencer', 'status', status)
    database.store('obs', {'sequencer_status': status})


def is_aborting() -> bool:
    return get_sequencer_status() in [
        SequencerStatus.ABORTING_USER, SequencerStatus.ABORTING_SOFTWARE
    ]


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


class WindowHintContextManager:
    def __init__(self, hint: WindowHint):
        self.hint = hint

    def __enter__(self):
        memory.hset('gui', 'window_hint', self.hint)

    def __exit__(self, exc_type, exc_val, exc_tb):
        memory.hdel('gui', 'window_hint')
