def ellipsis(string, length, ellipsis='...'):
    if len(string) > length:
        string = f'{string[:length - len(ellipsis)]}{ellipsis}'

    return string


def get_unit_string(metadata):
    unit = metadata.get('unit')
    if unit is None or unit == '':
        return ''
    elif unit == '°':
        return f'{unit}'
    else:
        return f' {unit}'


def get_service_name(unit):
    return unit.removeprefix('kalao_').removesuffix('.service')


def get_log_name(log):
    return log.removesuffix('_log').replace('_', ' ').upper()
