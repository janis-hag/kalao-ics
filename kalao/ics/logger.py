import traceback

from kalao.common.enums import LogLevel
from kalao.common.rprint import rprint

from kalao.ics import database


def info(name: str, message: str) -> None:
    log(name, LogLevel.INFO, message)


def warn(name: str, message: str) -> None:
    log(name, LogLevel.WARNING, message)


def error(name: str, message: str) -> None:
    log(name, LogLevel.ERROR, message)


def exception(name: str, exc: Exception) -> None:
    for lines in traceback.format_exception(exc):
        for message in lines.strip('\n').split('\n'):
            log(name, LogLevel.ERROR, message)


def log(name: str, level: LogLevel, message: str) -> None:
    rprint(f'{name.replace("_", " ").upper()} | [{level.value}] {message}',
           flush=True)

    database.store_log(name, level, message)
