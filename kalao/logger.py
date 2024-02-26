from kalao import database
from kalao.utils.rprint import rprint

from kalao.definitions.enums import LogLevel


def info(name: str, message: str) -> None:
    log(name, LogLevel.INFO, message)


def warn(name: str, message: str) -> None:
    log(name, LogLevel.WARNING, message)


def error(name: str, message: str) -> None:
    log(name, LogLevel.ERROR, message)


def log(name: str, level: LogLevel, message: str) -> None:
    rprint(f'{name.replace("_", " ").upper()} | [{level.value}] {message}',
           flush=True)

    database.store_log(name, level, message)
