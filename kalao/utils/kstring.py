import math
from typing import Any


def ellipsis(string: str, length: int, ellipsis: str = '...') -> str:
    if len(string) > length:
        string = f'{string[:length - len(ellipsis)]}{ellipsis}'

    return string


def get_unit_string(metadata: dict[str, Any]) -> str:
    unit = metadata.get('unit')
    if unit is None or unit == '':
        return ''
    elif unit == '°':
        return f'{unit}'
    else:
        return f' {unit}'


def get_service_name(unit: str) -> str:
    return unit.removeprefix('kalao_').removesuffix('.service')


def get_log_name(log: str) -> str:
    return log.removesuffix('_log').replace('_', ' ').upper()


def sec_to_dms(sec: float, decimal: int = 0) -> tuple[int, int, float | int]:
    if decimal == 0:
        sec = round(sec)
    else:
        sec = round(sec, decimal)

    deg = math.floor(sec / 3600)
    min = math.floor((sec/60) % 60)
    sec = sec % 60

    return deg, min, sec


def sec_to_dms_str(sec: float, decimal: int = 0, deg_str='°', min_str='\'',
                   sec_str='"') -> str:
    deg, min, sec = sec_to_dms(sec)

    if deg != 0:
        return f'{deg:d}{deg_str} {min:02d}{min_str} {sec:02.{decimal}f}{sec_str}'
    elif min != 0:
        return f'{min:d}{min_str} {sec:02.{decimal}f}"'
    else:
        return f'{sec:.{decimal}f}{sec_str}'


def sec_to_hms(sec: float, decimal: int = 0) -> tuple[int, int, float | int]:
    return sec_to_dms(sec)


def sec_to_hms_str(sec: float, decimal: int = 0) -> str:
    return sec_to_dms_str(sec, decimal=decimal, deg_str='h', min_str='m',
                          sec_str='s')
