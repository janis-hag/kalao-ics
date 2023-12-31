from kalao import database

from kalao.definitions.enums import LogLevel


def info(log, message):
    log(log, LogLevel.INFO, message)


def warn(log, message):
    log(log, LogLevel.WARNING, message)


def error(log, message):
    log(log, LogLevel.ERROR, message)


def log(log, level, message):
    log_name = log.replace('_', ' ').upper()

    print(f'{log_name:>14s} | [{level.value}] {message}', flush=True)

    database.store_log(log, level, message)