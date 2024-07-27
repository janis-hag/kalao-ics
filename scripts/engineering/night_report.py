import argparse
from datetime import date, datetime, time, timedelta

import pytz

from kalao.utils import ktime, report

from kalao.definitions.enums import ReportType

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Report Generator.')
    parser.add_argument('--long', action="store_false", dest="short",
                        help='Show everything')
    parser.add_argument('--sort', action="store", dest="sort",
                        default='failures,errors,warnings,key', help='Sorting')
    parser.add_argument('--type', action="store", dest="type",
                        default=ReportType.CLI, type=ReportType, help='Type')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--night', action="store", dest="night",
                       type=date.fromisoformat, help='Night')
    group.add_argument('--tonight', action="store_true", dest="tonight",
                       help='Tonight')

    args = parser.parse_args()

    if args.tonight:
        since = ktime.get_start_of_night()
    elif args.night is None:
        since = ktime.get_start_of_night()
        since = since - timedelta(days=1)
    else:
        since = datetime.combine(args.night, time(12, 0, 0, 0))
        since = pytz.timezone('America/Santiago').localize(since)

    print(
        report.generate(since, since + timedelta(days=1), short=args.short,
                        sort=args.sort, type=args.type))
