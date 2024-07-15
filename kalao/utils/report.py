import io
import sys
from datetime import datetime, timezone
from typing import Any

from kalao import database
from kalao.timers import monitoring
from kalao.utils import ktime

import pytz
from pymongo import DESCENDING
from systemd import journal

from kalao.definitions.enums import LogLevel

import config


def title(str_io: io.StringIO, title: str, level: int = 1) -> None:
    if level == 1:
        c = '='
    elif level == 2:
        c = '-'

    print(file=str_io)
    print(title, file=str_io)
    print(c * len(title), file=str_io)
    print(file=str_io)


def table_header(str_io: io.StringIO, headers: list[Any],
                 sizes: list[int]) -> None:
    print('┏━' + '━┳━'.join(['━' * s for s in sizes]) + '━┓', file=str_io)
    print(
        '┃ ' + ' ┃ '.join([f'{h:<{s}}'
                           for h, s in zip(headers, sizes)]) + ' ┃',
        file=str_io)
    print('┡━' + '━╇━'.join(["━" * s for s in sizes]) + '━┩', file=str_io)


def table_row(str_io: io.StringIO, rows: list[Any], sizes: list[int]) -> None:
    formaters = []
    formaters.append('<')
    for _ in range(len(sizes) - 1):
        formaters.append('>')

    print(
        '│ ' +
        ' │ '.join([f'{h:{f}{s}}'
                    for h, s, f in zip(rows, sizes, formaters)]) + ' │',
        file=str_io)


def table_footer(str_io: io.StringIO, sizes: list[int]) -> None:
    print('└─' + '─┴─'.join(['─' * s for s in sizes]) + '─┘', file=str_io)


def generate(since: datetime, until: datetime, short: bool = False,
             sort: str = 'failures,errors,warnings,key') -> str:
    with io.StringIO() as str_io:
        fmt = '%Y-%m-%d %H:%M:%S'

        if short:
            print(
                'Report mode: short. Only warnings and errors will be displayed.',
                file=str_io)
        else:
            print('Report mode: long', file=str_io)
        print(f'Generated: {datetime.now(timezone.utc).strftime(fmt)} UTC',
              file=str_io)

        title(str_io, 'Time')

        print(f'Night: {ktime.get_night_str(since)}', file=str_io)
        print(file=str_io)

        tz_cl = pytz.timezone('America/Santiago')
        tz_ch = pytz.timezone('Europe/Zurich')

        sizes = [5, 19, 19]
        table_header(str_io, [
            'UTC', f'CH/GVA ({since.astimezone(tz_ch).strftime("%z")})',
            f'CL/LSO ({since.astimezone(tz_cl).strftime("%z")})'
        ], sizes)
        table_row(str_io, [
            'Since',
            since.astimezone(timezone.utc).strftime(fmt),
            since.astimezone(tz_cl).strftime(fmt)
        ], sizes)
        table_row(str_io, [
            'Until',
            until.astimezone(timezone.utc).strftime(fmt),
            until.astimezone(tz_cl).strftime(fmt)
        ], sizes)
        table_footer(str_io, sizes)

        if sort is not None:
            sort_keys = sort.split(',')

            def sorting_fun(row):
                t = []
                for key in sort_keys:
                    if key not in row:
                        continue

                    if key in ['warnings', 'errors', 'failures']:
                        t.append(sys.maxsize - row[key])
                    else:
                        t.append(row[key])

                return tuple(t)
        else:

            def sorting_fun(row):
                return row['key']

        ##### Monitoring

        title(str_io, 'Monitoring')

        keys = sorted(
            list(database.definitions['monitoring']['metadata'].keys()))
        pipeline = [{
            '$match': {
                'metadata.key': {
                    '$in': keys
                },
                'timestamp': {
                    '$gte': since,
                    '$lte': until
                }
            }
        }, {
            '$sort': {
                'timestamp': DESCENDING
            }
        }]

        collection = database._get_collection('monitoring')
        cursor = collection.aggregate(pipeline)

        data = {}
        for document in cursor:
            key = document['metadata']['key']

            if key not in data:
                data[key] = []

            data[key].append({
                'timestamp': document['timestamp'],
                'value': document['value']
            })

        monitoring_stats = []

        for key in keys:
            points = 0
            warnings = 0
            errors = 0

            if key in data:
                points = len(data[key])

                for row in data[key]:
                    level, _, _ = monitoring.check_issues(key, row['value'])

                    if level == 'error':
                        errors += 1
                    elif level == 'warning':
                        warnings += 1

            if short and errors == 0 and warnings == 0:
                continue

            monitoring_stats.append({
                'key':
                    key,
                'short':
                    database.definitions['monitoring']['metadata'][key]
                    ['short'],
                'points':
                    points,
                'warnings':
                    warnings,
                'errors':
                    errors
            })

        sizes = [29, 8, 8, 8]
        table_header(str_io, ['Data', 'Points', 'Warnings', 'Errors'], sizes)

        for row in sorted(monitoring_stats, key=sorting_fun):
            table_row(str_io, [
                row['key'], row['points'], row['warnings'], row['errors']
            ], sizes)

        if len(monitoring_stats) == 0:
            table_row(str_io, ['Nothing to show', 'N/A', 'N/A', 'N/A'], sizes)

        table_footer(str_io, sizes)

        ##### Logs

        title(str_io, 'Logs')

        keys = sorted(list(database.definitions['logs']['metadata'].keys()))
        pipeline = [{
            '$match': {
                'metadata.key': {
                    '$in': keys
                },
                'timestamp': {
                    '$gte': since,
                    '$lte': until
                }
            }
        }, {
            '$sort': {
                'timestamp': DESCENDING
            }
        }]

        collection = database._get_collection('logs')
        cursor = collection.aggregate(pipeline)

        data = {}
        for document in cursor:
            key = document['metadata']['key']

            if key not in data:
                data[key] = []

            data[key].append({
                'origin': key,
                'timestamp': document['timestamp'],
                'level': document['level'],
                'message': document['message']
            })

        logs_stats = []
        messages = []

        for key in keys:
            if key == 'monitoring_timer_log':
                continue

            infos = 0
            warnings = 0
            errors = 0

            if key in data:
                for row in data[key]:
                    if row['level'] == LogLevel.ERROR:
                        errors += 1
                        messages.append(row)
                    elif row['level'] == LogLevel.WARNING:
                        warnings += 1
                        messages.append(row)
                    else:
                        if not short:
                            messages.append(row)
                        infos += 1

            if short and errors == 0 and warnings == 0:
                continue

            logs_stats.append({
                'key': key.removesuffix('_log').replace("_", " ").upper(),
                'infos': infos,
                'warnings': warnings,
                'errors': errors
            })

        sizes = [17, 8, 8, 8]
        table_header(str_io,
                     ['Log', LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR],
                     sizes)

        for row in sorted(logs_stats, key=sorting_fun):
            table_row(str_io, [
                row['key'], row['infos'], row['warnings'], row['errors']
            ], sizes)

        if len(monitoring_stats) == 0:
            table_row(str_io, ['Nothing to show', 'N/A', 'N/A', 'N/A'], sizes)

        table_footer(str_io, sizes)

        ##### Messages

        title(str_io, 'Log messages', level=2)

        if len(messages) == 0:
            print('No messages to show', file=str_io)
        else:
            print('All times are UTC', file=str_io)
            print(file=str_io)

        for message in sorted(messages, key=lambda row: row['timestamp']):
            timestamp = message['timestamp'].astimezone(
                timezone.utc).strftime(fmt)
            level = message['level']
            origin = message['origin'].removesuffix('_log').replace(
                "_", " ").upper()
            message = message['message']

            print(f'{timestamp} {origin:>17s} | [{level}] {message}',
                  file=str_io)

        ##### Services

        title(str_io, 'Services')

        keys = [
            service['unit'] for service in config.Systemd.services.values()
        ]

        reader = journal.Reader()

        for key in keys:
            reader.add_match(_SYSTEMD_USER_UNIT=key)
            reader.add_disjunction()
            reader.add_match(USER_UNIT=key)
            reader.add_disjunction()

        reader.seek_realtime(since)

        data = {}
        for entry in reader:
            if entry['__REALTIME_TIMESTAMP'] > until:
                break

            if 'UNIT_RESULT' in entry:
                key = entry['USER_UNIT']

                if key not in data:
                    data[key] = []

                data[key].append(entry)

        services_stats = []

        for key in keys:
            failures = 0

            if key in data:
                failures = len(data[key])

            if short and failures == 0:
                continue

            services_stats.append({
                'key': key.removesuffix('.service'),
                'failures': failures,
            })

        sizes = [24, 8]
        table_header(str_io, ['Service', 'Failures'], sizes)

        for row in sorted(services_stats, key=sorting_fun):
            table_row(str_io, [row['key'], row['failures']], sizes)

        if len(monitoring_stats) == 0:
            table_row(str_io, ['Nothing to show', 'N/A'], sizes)

        table_footer(str_io, sizes)

        return str_io.getvalue()
