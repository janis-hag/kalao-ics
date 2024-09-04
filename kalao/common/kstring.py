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


def sec_to_dms(sec: float,
               decimal: int = 0) -> tuple[int, int, int, float | int]:
    sign = 1 if sec >= 0 else -1
    sec = math.fabs(sec)

    if decimal == 0:
        sec = round(sec)
    else:
        sec = round(sec, decimal)

    min, sec = divmod(sec, 60)
    deg, min = divmod(min, 60)

    return sign, round(deg), round(min), sec


def sec_to_dms_str(sec: float, decimal: int = 0, deg_suffix: str = '°',
                   min_suffix: str = '\'', sec_suffix: str = '"',
                   short: bool = True) -> str:
    sign, deg, min, sec = sec_to_dms(sec, decimal=decimal)

    if decimal == 0:
        sec_format = '02d'
        sec_only_format = 'd'
    else:
        sec_format = f'0{decimal+3}.{decimal}f'
        sec_only_format = f'.{decimal}f'

    if sign < 0:
        sign_str = '-'
    else:
        sign_str = ''

    if deg != 0 or not short:
        return f'{sign_str}{deg:d}{deg_suffix} {min:02d}{min_suffix} {sec:{sec_format}}{sec_suffix}'
    elif min != 0:
        return f'{sign_str}{min:d}{min_suffix} {sec:{sec_format}}"'
    else:
        return f'{sign_str}{sec:{sec_only_format}}{sec_suffix}'


def sec_to_hms(sec: float,
               decimal: int = 0) -> tuple[int, int, int, float | int]:
    return sec_to_dms(sec, decimal=decimal)


def sec_to_hms_str(sec: float, decimal: int = 0, short=True) -> str:
    return sec_to_dms_str(sec, decimal=decimal, deg_suffix='h', min_suffix='m',
                          sec_suffix='s', short=short)
