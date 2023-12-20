import pprint
from datetime import datetime, timedelta

from systemd import journal

from kalao.definitions.enums import LogsOutputType, LogType

import config


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


def get_last_entries(reader, output_type=LogsOutputType.JSON):
    reader.process()

    entries = []
    for entry in reader:
        entries.append(process_entry(entry, output_type))

    return entries


def process_entry(entry, output_type=LogsOutputType.JSON):
    if output_type == LogsOutputType.RAW:
        return pprint.pformat(entry, indent=4)
    else:
        message = entry['MESSAGE']
        if message != '':
            type = LogType.INFO

            timestamp = entry['__REALTIME_TIMESTAMP'].strftime(
                '%y-%m-%d %H:%M:%S')

            if 'USER_UNIT' in entry:
                if '_COMM' in entry:
                    origin = entry['_COMM']
                else:
                    origin = entry['SYSLOG_IDENTIFIER']

                if entry.get('EXIT_STATUS', 0) != 0 or entry.get(
                        'UNIT_RESULT', '') == 'exit-code':
                    type = LogType.ERROR
            else:
                if '_SYSTEMD_USER_UNIT' in entry:
                    origin = entry['_SYSTEMD_USER_UNIT'].removeprefix(
                        'kalao_').removesuffix('.service')
                elif '_COMM' in entry:
                    origin = entry['_COMM']
                else:
                    return None

            if 'ERROR' in message or 'Failed' in message or 'Traceback' in message:
                type = LogType.ERROR
            elif 'WARNING' in message:
                type = LogType.WARNING

            return {
                'type': type,
                'timestamp': timestamp,
                'origin': origin,
                'message': message,
            }
