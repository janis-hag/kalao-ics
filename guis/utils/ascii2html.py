import re
from enum import StrEnum


class Category(StrEnum):
    FG_COLOR = 'fg-color'
    BG_COLOR = 'bg-color'
    INTENSITY = 'intensity'
    ITALIC = 'italic'
    UNDERLINE = 'underline'
    BLINKING = 'blinking'
    REVERSE = 'reverse'
    HIDDEN = 'hidden'
    STRIKETHROUGH = 'strikethrough'
    OVERLINE = 'overline'


default_state = {
    Category.FG_COLOR: None,
    Category.BG_COLOR: None,
    Category.INTENSITY: 0,
    Category.ITALIC: 0,
    Category.UNDERLINE: 0,
    Category.BLINKING: 0,
    Category.REVERSE: 0,
    Category.HIDDEN: 0,
    Category.STRIKETHROUGH: 0,
    Category.OVERLINE: 0
}


def _generate_substitution(codes, state):
    _handle_ansi_codes(codes, state)

    classes = []
    styles = []

    fg = state[Category.FG_COLOR]
    bg = state[Category.BG_COLOR]
    reverse = state[Category.REVERSE]

    color = fg if not reverse else bg
    if color is not None:
        if color.startswith('#'):
            styles.append(f'color: {color}')
        else:
            classes.append(color)

    color = bg if not reverse else fg
    if color is not None:
        if color.startswith('#'):
            styles.append(f'background-color: {color}')
        else:
            classes.append(color + '-bg')

    if state[Category.INTENSITY] == 1:
        classes.append('bold')
    elif state[Category.INTENSITY] == -1:
        classes.append('faint')

    if state[Category.ITALIC]:
        classes.append('italic')

    if state[Category.UNDERLINE] == 1:
        classes.append('underline')
    elif state[Category.UNDERLINE] == 2:
        classes.append('double-underline')

    if state[Category.BLINKING]:
        classes.append('blinking')

    if state[Category.HIDDEN]:
        classes.append('hidden')

    if state[Category.STRIKETHROUGH]:
        classes.append('strikethrough')

    if state[Category.OVERLINE]:
        classes.append('overline')

    html = ''

    if state['in_span']:
        html += '</span>'
        state['in_span'] = False

    if len(classes) != 0 or len(styles) != 0:
        html += '<span'

        if len(classes) != 0:
            html += f' class="{" ".join(classes)}"'

        if len(styles) != 0:
            html += f' style="{"; ".join(styles)}"'

        html += '>'
        state['in_span'] = True

    return html


def _handle_ansi_codes(codes, state):
    if codes == '':
        state.update(default_state)
        return

    codes = re.split(r'[;:]', codes)

    def convert(v):
        if v == '':
            return 0

        try:
            return int(v)
        except ValueError:
            return v

    codes = [convert(v) for v in codes]

    i = 0
    while i < len(codes):
        code = codes[i]

        # Basics

        if code == 0:
            state.update(default_state)

        elif code == 1:
            state[Category.INTENSITY] = 1

        elif code == 2:
            state[Category.INTENSITY] = -1

        elif code == 3:
            state[Category.ITALIC] = 1

        elif code == 4:
            state[Category.UNDERLINE] = 1

        elif code == 5:
            state[Category.BLINKING] = 1

        elif code == 6:
            state[Category.BLINKING] = 2

        elif code == 7:
            state[Category.REVERSE] = 1

        elif code == 8:
            state[Category.HIDDEN] = 1

        elif code == 9:
            state[Category.STRIKETHROUGH] = 1

        # Fonts

        # 10 to 20 are fonts (unsupported)

        elif code == 21:
            state[Category.UNDERLINE] = 2

        # Reset

        elif code == 22:
            state[Category.INTENSITY] = 0

        elif code == 23:
            state[Category.ITALIC] = 0

        elif code == 24:
            state[Category.UNDERLINE] = 0

        elif code == 25:
            state[Category.BLINKING] = 0

        elif code == 27:
            state[Category.REVERSE] = 0

        elif code == 28:
            state[Category.HIDDEN] = 0

        elif code == 29:
            state[Category.STRIKETHROUGH] = 0

        # Foreground

        elif 30 <= code <= 37:
            color = _get_8color(code - 30)
            if color is not None:
                state[Category.FG_COLOR] = color

        elif code == 38:
            color, incr = _get_256color_or_truecolor(codes, i)
            if color is not None:
                state[Category.FG_COLOR] = color
            i += incr

        elif code == 39:
            state[Category.FG_COLOR] = None

        # Background

        elif 40 <= code <= 47:
            color = _get_8color(code - 40)
            if color is not None:
                state[Category.BG_COLOR] = color

        elif code == 48:
            color, incr = _get_256color_or_truecolor(codes, i)
            if color is not None:
                state[Category.BG_COLOR] = color
            i += incr

        elif code == 49:
            state[Category.BG_COLOR] = None

        elif code == 53:
            state[Category.OVERLINE] = 1

        elif code == 55:
            state[Category.OVERLINE] = 0

        # Foreground bright

        elif 90 <= code <= 97:
            color = _get_8color(code - 90)
            if color is not None:
                state[Category.FG_COLOR] = color + '-bright'

        # Background bright

        elif 100 <= code <= 107:
            color = _get_8color(code - 100)
            if color is not None:
                state[Category.BG_COLOR] = color + '-bright'

        else:
            pass

        i += 1


def _get_8color(n):
    match n:
        case 0:
            return 'black'

        case 1:
            return 'red'

        case 2:
            return 'green'

        case 3:
            return 'yellow'

        case 4:
            return 'blue'

        case 5:
            return 'magenta'

        case 6:
            return 'cyan'

        case 7:
            return 'white'

        case _:
            return None


def _get_256color_or_truecolor(codes, i):
    try:
        if codes[i + 1] == 5:
            c = codes[i + 2]

            if 0 <= c <= 7:
                color = _get_8color(c)
            elif 8 <= c <= 15:
                color = _get_8color(c - 8) + '-bright'
            elif 16 <= c <= 231:
                b = (c-16) % 6
                g = ((c-16-b) // 6) % 6
                r = (c - 16 - b - 6*g) // 36

                color = f'#{r*51:02X}{g*51:02X}{b*51:02X}'
            elif 232 <= c <= 255:
                g = 8 + 10 * (c-232)

                color = f'#{g:02X}{g:02X}{g:02X}'
            else:
                color = None

            return color, 2

        elif codes[i + 1] == 2:
            r = codes[i + 2]
            g = codes[i + 3]
            b = codes[i + 4]

            color = f'#{r:02X}{g:02X}{b:02X}'

            return color, 4

        else:
            return None, 0

    except IndexError:
        return None, 0


def translate(text, close_last_span=True):
    # Escape HTML characters
    table = text.maketrans({
        '\n': '<br/>',
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        '\'': '&#39;',
    })
    text = text.translate(table)

    # Useless codes (https://invisible-island.net/xterm/ctlseqs/ctlseqs.html)
    replace_list = [
        '\u001b%@',  # ISO 8859-1 charset
        '\u001b%G',  # UTF-8 charset
        '\u001b\\(B',  # USASCII charset
    ]

    text = re.sub('(' + '|'.join(replace_list) + ')', '', text)

    state = {
        'in_span': False,
    } | default_state

    text = re.sub(
        re.compile(r'\u001b\[([0-9;]*)m'),
        lambda matchobj: _generate_substitution(matchobj.group(1), state),
        text)

    if state['in_span'] and close_last_span:
        text += '</span>'

    return text

stylesheet = \
    """
        * {
            white-space: pre;
        }
        
        .bold {
            font-weight: bold;
        }
        .faint {
            font-weight: 100;
        }
        .italic {
            font-style: italic;
        }
        .underline {
            text-decoration: underline;
        }
        .double-underline {
             text-decoration: underline double;
        }
        .hidden {
            visibility: hidden;
            opacity: 0;
        }
        .strikethrough {
            text-decoration: line-through;
        }
        .overline {
            text-decoration: overline;
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
