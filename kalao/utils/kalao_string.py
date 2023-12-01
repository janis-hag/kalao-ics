def ellipsis(string, length, ellipsis='...'):
    if len(string) > length:
        string = f'{string[:length - len(ellipsis)]}{ellipsis}'

    return string