from datetime import datetime, timedelta

from systemd import journal

from kalao.utils import kstring

from kalao.definitions.dataclasses import LogEntry
from kalao.definitions.enums import LogLevel

import config

# https://www.freedesktop.org/software/systemd/man/latest/systemd.journal-fields.html


def get_reader(filter: bool = True) -> journal.Reader:
    reader = journal.Reader()

    if filter:
        for service in config.Systemd.services.values():
            reader.add_match(_SYSTEMD_USER_UNIT=service['unit'])
            reader.add_disjunction()
            reader.add_match(USER_UNIT=service['unit'])
            reader.add_disjunction()

    return reader


def seek(reader: journal.Reader, entries_number: int = 50,
         entries_since_minutes: int | None = None) -> list[LogEntry]:
    if entries_since_minutes is not None:
        reader.seek_realtime(datetime.now() -
                             timedelta(minutes=entries_since_minutes))
    else:
        reader.seek_tail()
        reader.get_previous(skip=entries_number + 1)

    entries = []
    for entry in reader:
        entry_processed = process_entry(entry)

        if entry is not None:
            entries.append(entry_processed)

    return entries


def get_last_entries(reader: journal.Reader) -> list[LogEntry]:
    reader.process()

    entries = []
    for entry in reader:
        entry_processed = process_entry(entry)

        if entry is not None:
            entries.append(entry_processed)

    return entries


def get_entires_by_lines(lines: int, filter: bool = True) -> list[LogEntry]:
    reader = get_reader(filter=filter)
    reader.seek_tail()
    reader.get_previous(skip=lines + 1)

    entries = []
    for entry in reader:
        entry_processed = process_entry(entry)

        if entry is not None:
            entries.append(entry_processed)

    reader.close()

    return entries


def get_entries_since_cursor(cursor: str,
                             filter: bool = True) -> list[LogEntry]:
    reader = get_reader(filter=filter)
    reader.seek_cursor(cursor)
    reader.get_next()

    entries = []
    for entry in reader:
        entry_processed = process_entry(entry)

        if entry is not None:
            entries.append(entry_processed)

    reader.close()

    return entries


def get_entries_since_timestamp(timestamp: datetime | int | float,
                                filter: bool = True) -> list[LogEntry]:
    reader = get_reader(filter=filter)
    reader.seek_realtime(timestamp)
    reader.get_next()

    entries = []
    for entry in reader:
        entry_processed = process_entry(entry)

        if entry is not None:
            entries.append(entry_processed)

    reader.close()

    return entries


def get_entries_between(since: datetime, until: datetime,
                        filter: bool = True) -> list[LogEntry]:
    reader = get_reader(filter=filter)
    reader.seek_realtime(since)

    entries = []
    for entry in reader:
        if entry['__REALTIME_TIMESTAMP'] > until:
            break

        entry_processed = process_entry(entry)

        if entry is not None:
            entries.append(entry_processed)

    reader.close()

    return entries


def process_entry(entry: dict) -> LogEntry | None:
    message = entry['MESSAGE']

    if message != '':
        level = LogLevel.INFO

        if 'USER_UNIT' in entry:
            origin = kstring.get_service_name(entry['USER_UNIT'])

            if entry.get('EXIT_STATUS', 0) != 0 or entry.get(
                    'UNIT_RESULT', '') == 'exit-code':
                level = LogLevel.ERROR

        elif '_SYSTEMD_USER_UNIT' in entry:
            origin = kstring.get_service_name(entry['_SYSTEMD_USER_UNIT'])

        else:
            return None

        if 'ERROR' in message or 'Failed' in message or 'Traceback' in message:
            level = LogLevel.ERROR
        elif 'WARNING' in message:
            level = LogLevel.WARNING

        if origin == 'cacao' and '_SYSTEMD_USER_UNIT' in entry:
            # Inhibit errors and warnings from cacao scripts as they output too many non-relevant ones
            level = LogLevel.INFO

        return LogEntry(cursor=entry['__CURSOR'], level=level,
                        timestamp=entry['__REALTIME_TIMESTAMP'], origin=origin,
                        message=message)
