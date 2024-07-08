import argparse
import sys
from datetime import date, datetime, time, timedelta, timezone

from kalao import database
from kalao.timers import monitoring
from kalao.utils import ktime

import pytz
from pymongo import DESCENDING

from kalao.definitions.enums import LogLevel


def print_title(title, level=1):
    if level == 1:
        c = '='
    elif level == 2:
        c = '-'

    print()
    print(title)
    print(c * len(title))
    print()


def generate_summary(since: datetime, until: datetime, short=False,
                     sort='key'):
    fmt = '%Y-%m-%d %H:%M:%S'

    if short:
        print(
            'Report mode: short. Only warnings and errors will be displayed.')
    else:
        print('Report mode: long')
    print(f'Generated: {datetime.now(timezone.utc).strftime(fmt)} UTC')

    print_title('Time')

    print(f'Night: {ktime.get_night_str(since)}')
    print()

    tz_cl = pytz.timezone('America/Santiago')
    tz_ch = pytz.timezone('Europe/Zurich')

    print(
        '┏━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┓'
    )
    print(
        f'┃       ┃ UTC                 ┃ CH/GVA ({since.astimezone(tz_ch).strftime("%z")})      ┃ CL/LSO ({since.astimezone(tz_cl).strftime("%z")})      ┃'
    )
    print(
        '┡━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━┩'
    )
    print(
        f'│ Since │ {since.astimezone(timezone.utc).strftime(fmt)} │ {since.astimezone(tz_ch).strftime(fmt)} │ {since.astimezone(tz_cl).strftime(fmt)} │'
    )
    print(
        f'│ Until │ {until.astimezone(timezone.utc).strftime(fmt)} │ {until.astimezone(tz_ch).strftime(fmt)} │ {until.astimezone(tz_cl).strftime(fmt)} │'
    )
    print(
        '└───────┴─────────────────────┴─────────────────────┴─────────────────────┘'
    )

    if sort is not None:
        sort_keys = sort.split(',')

        def sorting_fun(row):
            t = []
            for key in sort_keys:
                if key in ['warnings', 'errors']:
                    t.append(sys.maxsize - row[key])
                else:
                    t.append(row[key])

            return tuple(t)
    else:

        def sorting_fun(row):
            return row['key']

    ##### Monitoring

    print_title('Monitoring')

    keys = sorted(list(database.definitions['monitoring']['metadata'].keys()))
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
        warnings = 0
        errors = 0

        if key not in data:
            points = 0
        else:
            points = len(data[key])

            for row in data[key]:
                level, _, _ = monitoring.check_warning_error(key, row['value'])

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
                database.definitions['monitoring']['metadata'][key]['short'],
            'points':
                points,
            'warnings':
                warnings,
            'errors':
                errors
        })

    print(f'┏━{"━" * 29}━┳━{"━" * 8}━┳━{"━" * 8}━┳━{"━" * 8}━┓')
    print(
        f'┃ {"Data": <29s} ┃ {"Points": <8s} ┃ {"Warnings": <8s} ┃ {"Errors": <8s} ┃'
    )
    print(f'┡━{"━" * 29}━╇━{"━" * 8}━╇━{"━" * 8}━╇━{"━" * 8}━┩')

    for row in sorted(monitoring_stats, key=sorting_fun):
        key = row['key']
        points = row['points']
        warnings = row['warnings']
        errors = row['errors']

        print(
            f'│ {key: <29s} │ {points:>8d} │ {warnings:>8d} │ {errors:>8d} │')

    if len(monitoring_stats) == 0:
        print(
            f'│ {"Nothing to show": <29s} │ {"N/A":>8s} │ {"N/A":>8s} │ {"N/A":>8s} │'
        )

    print(f'└─{"─"*29}─┴─{"─"*8}─┴─{"─"*8}─┴─{"─"*8}─┘')

    ##### Logs

    print_title('Logs')

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

        key = key.removesuffix('_log').replace("_", " ").upper()

        if short and errors == 0 and warnings == 0:
            continue

        logs_stats.append({
            'key': key,
            'infos': infos,
            'warnings': warnings,
            'errors': errors
        })

    print(f'┏━{"━" * 17}━┳━{"━" * 8}━┳━{"━" * 8}━┳━{"━" * 8}━┓')
    print(
        f'┃ {"Log": <17s} ┃ {LogLevel.INFO: <8s} ┃ {LogLevel.WARNING: <8s} ┃ {LogLevel.ERROR: <8s} ┃'
    )
    print(f'┡━{"━" * 17}━╇━{"━" * 8}━╇━{"━" * 8}━╇━{"━" * 8}━┩')

    for row in sorted(logs_stats, key=sorting_fun):
        key = row['key']
        infos = row['infos']
        warnings = row['warnings']
        errors = row['errors']

        print(f'│ {key: <17s} │ {infos:>8d} │ {warnings:>8d} │ {errors:>8d} │')

    if len(logs_stats) == 0:
        print(
            f'│ {"Nothing to show": <17s} │ {"N/A":>8s} │ {"N/A":>8s} │ {"N/A":>8s} │'
        )

    print(f'└─{"─"*17}─┴─{"─"*8}─┴─{"─"*8}─┴─{"─"*8}─┘')

    ##### Messages

    print_title('Log messages', level=2)

    if len(messages) == 0:
        print('No log messages to show')
    else:
        print("All times are UTC")
        print()

    for message in sorted(messages, key=lambda row: row['timestamp']):
        timestamp = message['timestamp'].astimezone(timezone.utc).strftime(fmt)
        level = message['level']
        origin = message['origin'].removesuffix('_log').replace("_",
                                                                " ").upper()
        message = message['message']

        print(f'{timestamp} {origin:>17s} | [{level}] {message}')

    return monitoring_stats, logs_stats, messages


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Report Generator.')
    parser.add_argument('--long', action="store_false", dest="short",
                        help='Show everything')
    parser.add_argument('--sort', action="store", dest="sort",
                        default='errors,warnings,key', help='Sorting')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--night', action="store", dest="night",
                       type=date.fromisoformat, help='Night')
    group.add_argument('--tonight', action="store_true", dest="tonight",
                       help='Tonight')

    args = parser.parse_args()

    if args.tonight:
        start = ktime.get_start_of_night()
    elif args.night is None:
        start = ktime.get_start_of_night()
        start = start - timedelta(days=1)
    else:
        start = datetime.combine(args.night, time(12, 0, 0, 0))
        start = pytz.timezone('America/Santiago').localize(start)

    generate_summary(start, start + timedelta(days=1), short=args.short,
                     sort=args.sort)
