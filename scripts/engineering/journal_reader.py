import argparse
import select

from kalao import logs
from kalao.utils.terminal_colors import TerminalColors as TC

from kalao.definitions.enums import LogLevel


def run(args):
    reader = logs.get_reader(args.filter)

    poll = select.poll()
    poll.register(reader, reader.get_events())

    for entry in logs.seek(reader, args.entries_number, args.entries_since):
        format_entry(entry)

    while poll.poll():
        for entry in logs.get_last_entries(reader):
            format_entry(entry)


def format_entry(entry):
    style_timestamp = TC.WHITE
    style_origin = ''
    style_message = ''
    style_end = TC.RESET

    if entry.level == LogLevel.ERROR:
        style_origin = TC.BOLD + TC.BRIGHT_RED + TC.BLINK
        style_message = TC.BOLD + TC.BRIGHT_RED
    elif entry.level == LogLevel.WARNING:
        style_message = TC.BOLD + TC.BRIGHT_YELLOW,

    print(
        f'{style_timestamp}{entry.timestamp}{style_end} {style_origin}{entry.origin:>17s}{style_end}: {style_message}{entry.message}{style_end}'
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=
        'Display system journal with colors and a more practical format.')
    parser.add_argument('--no-filter', action="store_false", dest="filter",
                        help='Disable filtering')
    parser.add_argument('-n', action="store", dest="entries_number",
                        default=50, type=int,
                        help='Initially show <n> entries')
    parser.add_argument('--since', action="store", dest="entries_since",
                        default=None, type=float,
                        help='Initially show entries since <s> minutes')

    args = parser.parse_args()

    run(args)
