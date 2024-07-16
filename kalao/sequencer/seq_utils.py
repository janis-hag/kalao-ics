from functools import wraps
from typing import Any, Callable

from kalao import database, memory

from kalao.definitions.enums import SequencerStatus


def get_sequencer_status() -> SequencerStatus:
    return SequencerStatus(
        memory.get('sequencer_status', default=SequencerStatus.UNKNOWN))


def set_sequencer_status(status: SequencerStatus) -> None:
    memory.set('sequencer_status', str(status))
    database.store('obs', {'sequencer_status': status})


def is_aborting() -> bool:
    status = get_sequencer_status()
    return status == SequencerStatus.ABORTING or status == SequencerStatus.ABORTING_ERROR


def with_sequencer_status(status: SequencerStatus) -> Any:
    def _with_sequencer_status(fun: Callable) -> Any:
        @wraps(fun)
        def wrapper(*args: tuple[Any, ...], **kwargs: dict[str, Any]) -> Any:
            ret = None
            exception = None

            previous_status = get_sequencer_status()
            set_sequencer_status(status)

            try:
                ret = fun(*args, **kwargs)
            except Exception as e:
                exception = e

            current_status = get_sequencer_status()

            # Restore previous status if status didn't change
            # (e.g. do not change if status was switched to ABORTING or ERROR)
            if current_status == status:
                set_sequencer_status(previous_status)

            if exception is not None:
                raise exception

            return ret

        return wrapper

    return _with_sequencer_status
