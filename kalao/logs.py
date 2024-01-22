import pprint
from datetime import datetime, timedelta

from kalao.utils import kstring

from systemd import journal

from kalao.definitions.enums import LogLevel, LogsOutputType

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


def seek(reader, output_type=LogsOutputType.JSON, entries_number=50,
         entries_since_minutes=None):
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


def get_entries_between(since, until, filter=True,
                        output_type=LogsOutputType.JSON):
    reader = get_reader(filter=filter)
    reader.seek_realtime(since)

    entries = []
    for entry in reader:
        if entry['__REALTIME_TIMESTAMP'] > until:
            break

        entries.append(process_entry(entry, output_type))

    return entries


def process_entry(entry, output_type=LogsOutputType.JSON):
    if output_type == LogsOutputType.RAW:
        return pprint.pformat(entry, indent=4)
    else:
        message = entry['MESSAGE']
        if message != '':
            level = LogLevel.INFO

            timestamp = entry['__REALTIME_TIMESTAMP'].strftime(
                '%y-%m-%d %H:%M:%S')

            if 'USER_UNIT' in entry:
                if '_COMM' in entry:
                    origin = entry['_COMM']
                else:
                    origin = entry['SYSLOG_IDENTIFIER']

                if entry.get('EXIT_STATUS', 0) != 0 or entry.get(
                        'UNIT_RESULT', '') == 'exit-code':
                    level = LogLevel.ERROR
            else:
                if '_SYSTEMD_USER_UNIT' in entry:
                    origin = kstring.get_service_name(
                        entry['_SYSTEMD_USER_UNIT'])
                elif '_COMM' in entry:
                    origin = entry['_COMM']
                else:
                    return None

            if 'ERROR' in message or 'Failed' in message or 'Traceback' in message:
                level = LogLevel.ERROR
            elif 'WARNING' in message:
                level = LogLevel.WARNING

            return {
                'level': level,
                'timestamp': timestamp,
                'origin': origin,
                'message': message,
            }
