import re


def translate(str):
    pattern = re.compile(r"\u001b\[([0-9]+)m")
    nb_span = 0

    # Escape HTML characters
    table = str.maketrans({
        '\n': '<br/>',
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        '\'': '&#39;',
    })
    str = str.translate(table)

    def dashrepl(matchobj):
        nonlocal nb_span

        nb_span += 1

        match matchobj.group(1):
            case '0':
                str = '</span>' * (nb_span-1)
                nb_span = 0
                return str

            case '1':
                return '<span class="bold">'

            case '3':
                return '<span class="italic">'

            case '4':
                return '<span class="underline">'

            case '9':
                return '<span class="crossed">'

            # Foreground

            case '30':
                return '<span class="black">'

            case '31':
                return '<span class="red">'

            case '32':
                return '<span class="green">'

            case '33':
                return '<span class="yellow">'

            case '34':
                return '<span class="blue">'

            case '35':
                return '<span class="magenta">'

            case '36':
                return '<span class="cyan">'

            case '37':
                return '<span class="white">'

            # Background

            case '40':
                return '<span class="black-bg">'

            case '41':
                return '<span class="red-bg">'

            case '42':
                return '<span class="green-bg">'

            case '43':
                return '<span class="yellow-bg">'

            case '44':
                return '<span class="blue-bg">'

            case '45':
                return '<span class="magenta-bg">'

            case '46':
                return '<span class="cyan-bg">'

            case '47':
                return '<span class="white-bg">'

            # Foreground bright

            case '90':
                return '<span class="black-bright">'

            case '91':
                return '<span class="red-bright">'

            case '92':
                return '<span class="green-bright">'

            case '93':
                return '<span class="yellow-bright">'

            case '94':
                return '<span class="blue-bright">'

            case '95':
                return '<span class="magenta-bright">'

            case '96':
                return '<span class="cyan-bright">'

            case '97':
                return '<span class="white-bright">'

            # Background bright

            case '100':
                return '<span class="black-bright-bg">'

            case '101':
                return '<span class="red-bright-bg">'

            case '102':
                return '<span class="green-bright-bg">'

            case '103':
                return '<span class="yellow-bright-bg">'

            case '104':
                return '<span class="blue-bright-bg">'

            case '105':
                return '<span class="magenta-bright-bg">'

            case '106':
                return '<span class="cyan-bright-bg">'

            case '107':
                return '<span class="white-bright-bg">'

            case _:
                return '<span>'

    str = re.sub(pattern, dashrepl, str)

    return str

stylesheet = \
    """
        span {
            white-space: pre;
        }
        
        .bold {
            font-weight: bold;
        }
        .italic {
            font-style: italic;
        }
        .underline {
            text-decoration: underline;
        }
        .crossed {
            text-decoration: line-through;
        }
        
        .black {
            color: #232627;
        }
        .red {
            color: #ed1515;
        }
        .green {
            color: #11d116;
        }
        .yellow {
            color: #f67400;
        }
        .blue {
            color: #1d99f3;
        }
        .magenta {
            color: #9b59b6;
        }
        .cyan {
            color: #1abc9c;
        }
        .white {
            color: #fcfcfc;
        }
        
        .black-bg {
            background-color: #232627;
        }
        .red-bg {
            background-color: #ed1515;
        }
        .green-bg {
            background-color: #11d116;
        }
        .yellow-bg {
            background-color: #f67400;
        }
        .blue-bg {
            background-color: #1d99f3;
        }
        .magenta-bg {
            background-color: #9b59b6;
        }
        .cyan-bg {
            background-color: #1abc9c;
        }
        .white-bg {
            background-color: #fcfcfc;
        }
        
        .black-bright {
            color: #7f8c8d;
        }
        .red-bright {
            color: #c0392b;
        }
        .green-bright {
            color: #1cdc9a;
        }
        .yellow-bright {
            color: #fdbc4b;
        }
        .blue-bright {
            color: #3daee9;
        }
        .magenta-bright {
            color: #8e44ad;
        }
        .cyan-bright {
            color: #16a085;
        }
        .white-bright {
            color: #ffffff;
        }
        
        .black-bright-bg {
            background-color: #7f8c8d;
        }
        .red-bright-bg {
            background-color: #c0392b;
        }
        .green-bright-bg {
            background-color: #1cdc9a;
        }
        .yellow-bright-bg {
            background-color: #fdbc4b;
        }
        .blue-bright-bg {
            background-color: #3daee9;
        }
        .magenta-bright-bg {
            background-color: #8e44ad;
        }
        .cyan-bright-bg {
            background-color: #16a085;
        }
        .white-bright-bg {
            background-color: #ffffff;
        }
    """
