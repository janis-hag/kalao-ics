from kalao.utils import database


def print_and_log(message):
    database.store('obs', {'sequencer_log': message})
