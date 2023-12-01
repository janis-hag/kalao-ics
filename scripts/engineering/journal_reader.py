import argparse
import select

from kalao import logs

from kalao.definitions.enums import LogsOutputType


def run(args):
    reader = logs.get_reader(args.filter)

    poll = select.poll()
    poll.register(reader, reader.get_events())

    for entry in logs.seek(reader, args.type, args.entries_number,
                           args.entries_since):
        print(entry)

    while poll.poll():
        for entry in logs.get_last_entries(reader, args.type):
            print(entry)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Display system journal.')
    parser.add_argument('--no-filter', action="store_false", dest="filter",
                        help='Disable filtering')
    parser.add_argument('--raw', action="store_true", dest="type",
                        help='Display raw entries')
    parser.add_argument('-n', action="store", dest="entries_number",
                        default=50, type=int,
                        help='Initially show <n> entries')
    parser.add_argument('--since', action="store", dest="entries_since",
                        default=None, type=float,
                        help='Initially show entries since <s> minutes')

    args = parser.parse_args()

    if args.type:
        args.type = LogsOutputType.RAW
    else:
        args.type = LogsOutputType.TEXT

    run(args)
