from functools import wraps

from kalao import database


def with_sequencer_status(status):
    def _with_sequencer_status(fun):
        @wraps(fun)
        def wrapper(*args, **kwargs):
            previous_status = database.get_last_value('obs',
                                                      'sequencer_status')
            database.store('obs', {'sequencer_status': status})

            ret = fun(*args, **kwargs)

            current_status = database.get_last_value('obs', 'sequencer_status')

            # Restore previous status if status didn't change
            # (e.g. do not change if status was switched to ABORTING or ERROR)
            if current_status == status:
                database.store('obs', {'sequencer_status': previous_status})

            return ret

        return wrapper

    return _with_sequencer_status
