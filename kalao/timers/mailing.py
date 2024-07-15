import threading
import time
from datetime import timedelta
from typing import Callable

from kalao import email, logger
from kalao.utils import ktime, report

import schedule


def _send_night_report() -> None:

    since = ktime.get_start_of_night()
    since = since - timedelta(days=1)

    night_str = ktime.get_night_str(since)

    logger.info('monitoring_timer',
                f'Sending daily night report for night {night_str}')

    message = report.generate(since, since + timedelta(days=1), short=True)

    email.send_email(f'KalAO Night Report {night_str}', message)


if __name__ == '__main__':

    def run_threaded(job_func: Callable) -> None:
        job_thread = threading.Thread(target=job_func)
        job_thread.start()

    schedule.every().day.at('13:00',
                            'America/Santiago').do(run_threaded,
                                                   _send_night_report)

    while True:
        n = schedule.idle_seconds()

        if n is None:
            break
        elif n > 0:
            time.sleep(n)

        schedule.run_pending()
