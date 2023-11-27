import pprint
from datetime import datetime, timedelta

from kalao.utils.terminal_colors import TerminalColors as TC

from systemd import journal

from kalao.definitions.enums import LogsOutputType

import config

styles = {
    LogsOutputType.TEXT: {
        'message_init': '',
        'origin_init': '',
        'origin_error': TC.BOLD + TC.BRIGHT_RED + TC.BLINK,
        'message_error': TC.BOLD + TC.BRIGHT_RED,
        'message_warning': TC.BOLD + TC.BRIGHT_YELLOW,
        'message_good': TC.BRIGHT_GREEN,
        'end': TC.RESET,
    },
    LogsOutputType.HTML: {
        'message_init': '<span>',
        'origin_init': '<span>',
        'origin_error': '<span class="red">',
        'message_error': '<span class="red">',
        'message_warning': '<span class="yellow">',
        'message_good': '<span class="green">',
        'end': '</span>',
    },
}


def get_reader(filter=True):
    reader = journal.Reader()

    if filter:
        for service in config.Systemd.services.values():
            reader.add_match(_SYSTEMD_USER_UNIT=service['unit'])
            reader.add_disjunction()
            reader.add_match(USER_UNIT=service['unit'])
            reader.add_disjunction()

    return reader


def seek(reader, output_type, entries_number=50, entries_since_minutes=None):
    if entries_since_minutes is not None:
        reader.seek_realtime(datetime.now() -
                             timedelta(minutes=entries_since_minutes))
    else:
        reader.seek_tail()
        reader.get_previous(skip=entries_number + 1)

    entries = []
    for entry in reader:
        entries.append(process_entry(entry, output_type))

    return entries


def get_last_entries(reader, output_type):
    if reader.process() != reader.APPEND:
        return []

    entries = []
    for entry in reader:
        entries.append(process_entry(entry, output_type))

    return entries


def process_entry(entry, output_type):
    if output_type == LogsOutputType.RAW:
        return pprint.pformat(entry, indent=4)
    else:
        message = entry["MESSAGE"]
        if message != "":
            style = styles[output_type]

            style_message = style['message_init']
            style_origin = style['origin_init']
            style_end = style["end"]

            timestamp = entry["__REALTIME_TIMESTAMP"].strftime(
                "%y-%m-%d %H:%M:%S")

            if 'USER_UNIT' in entry:
                origin = entry["_COMM"]

                if entry.get('EXIT_STATUS', 0) != 0 or entry.get(
                        'UNIT_RESULT', '') == 'exit-code':
                    style_message = style['message_error']
                    style_origin = style['origin_error']
                else:
                    style_message = style['message_good']
            else:
                origin = entry["_SYSTEMD_USER_UNIT"].replace(
                    'kalao_', '').replace('.service', '')

            if '[ERROR]' in message:
                style_message = style['message_error']
                style_origin = style['origin_error']
            elif '[WARNING]' in message:
                style_message = style['message_warning']

            if output_type == LogsOutputType.HTML:
                return {
                    'timestamp': timestamp,
                    'origin': f'{style_origin}{origin}{style_end}',
                    'message': f'{style_message}{message}{style_end}',
                }
            else:
                return f'{timestamp} {style_origin}{origin:>15s}{style_end}: {style_message}{message}{style_end}'
