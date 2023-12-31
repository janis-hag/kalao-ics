from kalao import database

from kalao.definitions.enums import LogLevel


def info(name, message):
    log(name, LogLevel.INFO, message)


def warn(name, message):
    log(name, LogLevel.WARNING, message)


def error(name, message):
    log(name, LogLevel.ERROR, message)


def log(name, level, message):
    print(f'{name.replace("_", " ").upper():>14s} | [{level.value}] {message}',
          flush=True)

    database.store_log(name, level, message)
