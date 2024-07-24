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

from kalao.definitions.enums import AlarmLevel, LogLevel, ReportType

import config

_print = print


def print(str_io: io.StringIO, text: str = '',
          type: ReportType = ReportType.CLI):
    if type == ReportType.HTML:
        _print(f'{text}<br/>', file=str_io)
    else:
        _print(text, file=str_io)


def start_document(str_io: io.StringIO, type: ReportType = ReportType.CLI):
    if type == ReportType.HTML:
        _print(
            """\
<html>
    <head>
        <style>
            table, th, td {
                border: 1px solid black;
                border-collapse: collapse;
            }
            
            th, td {
                text-align: left;
                padding: 5px;
            }
            
            .align-right {
                text-align: right;
            }
            
            pre {
                font: monospace;
            }
        </style>
    </head>
    <body>""", file=str_io)


def end_document(str_io: io.StringIO, type: ReportType = ReportType.CLI):
    if type == ReportType.HTML:
        _print("""\
    </body>
</html>""", file=str_io)


def start_code(str_io: io.StringIO, type: ReportType = ReportType.CLI):
    if type == ReportType.HTML:
        _print('<pre>', file=str_io)


def print_code(str_io: io.StringIO, text: str = '',
               type: ReportType = ReportType.CLI):
    if type == ReportType.HTML:
        _print(text, file=str_io)
    else:
        _print(text, file=str_io)


def end_code(str_io: io.StringIO, type: ReportType = ReportType.CLI):
    if type == ReportType.HTML:
        _print('</pre>', file=str_io)


def title(str_io: io.StringIO, title: str, level: int = 1,
          type: ReportType = ReportType.CLI) -> None:
    if type == ReportType.HTML:
        _print(f'<h{level}>{title}</h{level}>', file=str_io)
    else:
        if level == 1:
            c = '='
        elif level == 2:
            c = '-'

        _print(file=str_io)
        _print(title, file=str_io)
        _print(c * len(title), file=str_io)
        _print(file=str_io)


def table_header(str_io: io.StringIO, headers: list[Any], sizes: list[int],
                 type: ReportType = ReportType.CLI) -> None:
    if type == ReportType.HTML:
        _print(
            '<table><thead><tr>' + ''.join([f'<th>{h}</th>'
                                            for h in headers]) +
            '</tr></thead>', file=str_io)
    else:
        _print('┏━' + '━┳━'.join(['━' * s for s in sizes]) + '━┓', file=str_io)
        _print(
            '┃ ' + ' ┃ '.join([f'{h:<{s}}'
                               for h, s in zip(headers, sizes)]) + ' ┃',
            file=str_io)
        _print('┡━' + '━╇━'.join(["━" * s for s in sizes]) + '━┩', file=str_io)


def table_row(str_io: io.StringIO, rows: list[Any], sizes: list[int],
              type: ReportType = ReportType.CLI) -> None:
    if type == ReportType.HTML:
        formaters = []
        formaters.append('align-left')
        for _ in range(len(sizes) - 1):
            formaters.append('align-right')

        _print(
            '<tr>' + ''.join(
                [f'<td class="{f}">{r}</td>'
                 for r, f in zip(rows, formaters)]) + '</tr>', file=str_io)
    else:
        formaters = []
        formaters.append('<')
        for _ in range(len(sizes) - 1):
            formaters.append('>')

        _print(
            '│ ' + ' │ '.join(
                [f'{h:{f}{s}}'
                 for h, s, f in zip(rows, sizes, formaters)]) + ' │',
            file=str_io)


def table_footer(str_io: io.StringIO, sizes: list[int],
                 type: ReportType = ReportType.CLI) -> None:
    if type == ReportType.HTML:
        _print('</table>', file=str_io)
    else:
        _print('└─' + '─┴─'.join(['─' * s for s in sizes]) + '─┘', file=str_io)


def generate(since: datetime, until: datetime, short: bool = False,
             sort: str = 'failures,alarms,errors,warnings,key',
             type=ReportType.CLI) -> str:
    with io.StringIO() as str_io:
        start_document(str_io, type=type)

        fmt = '%Y-%m-%d %H:%M:%S'

        if short:
            print(
                str_io,
                'Report mode: short. Only warnings, errors, alarms and failures will be displayed.',
                type=type)
        else:
            print(str_io, 'Report mode: long.', type=type)
        print(str_io,
              f'Generated: {datetime.now(timezone.utc).strftime(fmt)} UTC',
              type=type)

        for repo in config.Git.repositories:
            if '-dirty' in config.get_git_version(repo):
                print(
                    str_io,
                    f'Warning: {repo} git repository contains uncommited changes.',
                    type=type)

        title(str_io, 'Time', type=type)

        print(str_io, f'Night: {ktime.get_night_str(since)}', type=type)
        print(str_io, type=type)

        tz_cl = pytz.timezone('America/Santiago')
        tz_ch = pytz.timezone('Europe/Zurich')

        sizes = [5, 19, 19, 19]
        table_header(str_io, [
            '', 'UTC', f'CH/GVA ({since.astimezone(tz_ch).strftime("%z")})',
            f'CL/LSO ({since.astimezone(tz_cl).strftime("%z")})'
        ], sizes, type=type)
        table_row(str_io, [
            'Since',
            since.astimezone(timezone.utc).strftime(fmt),
            since.astimezone(tz_ch).strftime(fmt),
            since.astimezone(tz_cl).strftime(fmt)
        ], sizes, type=type)
        table_row(str_io, [
            'Until',
            until.astimezone(timezone.utc).strftime(fmt),
            until.astimezone(tz_ch).strftime(fmt),
            until.astimezone(tz_cl).strftime(fmt)
        ], sizes, type=type)
        table_footer(str_io, sizes, type=type)

        if sort is not None:
            sort_keys = sort.split(',')

            def sorting_fun(row):
                t = []
                for key in sort_keys:
                    if key not in row:
                        continue

                    if key in ['warnings', 'errors', 'alarms', 'failures']:
                        t.append(sys.maxsize - row[key])
                    else:
                        t.append(row[key])

                return tuple(t)
        else:

            def sorting_fun(row):
                return row['key']

        ##### Monitoring

        title(str_io, 'Monitoring', type=type)

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
            alarms = 0

            if key in data:
                points = len(data[key])

                for row in data[key]:
                    level, _, _ = monitoring.check_alarms(key, row['value'])

                    if level == AlarmLevel.ALARM:
                        alarms += 1
                    elif level == AlarmLevel.WARNING:
                        warnings += 1

            if short and alarms == 0 and warnings == 0:
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
                'alarms':
                    alarms
            })

        sizes = [29, 8, 8, 8]
        table_header(str_io, ['Data', 'Points', 'Warnings', 'Alarms'], sizes,
                     type=type)

        for row in sorted(monitoring_stats, key=sorting_fun):
            table_row(str_io, [
                row['key'], row['points'], row['warnings'], row['alarms']
            ], sizes, type=type)

        if len(monitoring_stats) == 0:
            table_row(str_io, ['Nothing to show', 'N/A', 'N/A', 'N/A'], sizes,
                      type=type)

        table_footer(str_io, sizes, type=type)

        ##### Services

        title(str_io, 'Services', type=type)

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
        table_header(str_io, ['Service', 'Failures'], sizes, type=type)

        for row in sorted(services_stats, key=sorting_fun):
            table_row(str_io, [row['key'], row['failures']], sizes, type=type)

        if len(services_stats) == 0:
            table_row(str_io, ['Nothing to show', 'N/A'], sizes, type=type)

        table_footer(str_io, sizes, type=type)

        ##### Logs

        title(str_io, 'Logs', type=type)

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
                'key': key.removesuffix('_log').replace('_', ' ').upper(),
                'infos': infos,
                'warnings': warnings,
                'errors': errors
            })

        sizes = [17, 8, 8, 8]
        table_header(str_io,
                     ['Log', LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR],
                     sizes, type=type)

        for row in sorted(logs_stats, key=sorting_fun):
            table_row(str_io, [
                row['key'], row['infos'], row['warnings'], row['errors']
            ], sizes, type=type)

        if len(logs_stats) == 0:
            table_row(str_io, ['Nothing to show', 'N/A', 'N/A', 'N/A'], sizes,
                      type=type)

        table_footer(str_io, sizes, type=type)

        ##### Messages

        title(str_io, 'Log messages', level=2, type=type)

        start_code(str_io, type=type)
        if len(messages) == 0:
            print_code(str_io, 'No messages to show', type=type)
        else:
            print_code(str_io, 'All times are UTC', type=type)
            print_code(str_io, type=type)

        for message in sorted(messages, key=lambda row: row['timestamp']):
            timestamp = message['timestamp'].astimezone(
                timezone.utc).strftime(fmt)
            level = message['level']
            origin = message['origin'].removesuffix('_log').replace(
                "_", " ").upper()
            message = message['message']

            print_code(str_io,
                       f'{timestamp} {origin:>17s} | [{level}] {message}',
                       type=type)
        end_code(str_io, type=type)

        end_document(str_io, type=type)

        return str_io.getvalue()
