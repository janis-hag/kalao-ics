import time

from kalao import database, logger
from kalao.utils import kalao_time

import config

start_time = kalao_time.now()
tick = 0

while True:
    ellapsed_time = (kalao_time.now() - start_time).total_seconds()

    if ellapsed_time > 86400:
        logger.info(
            'safety_timer',
            'Killing safety dead-man as it has been running since more than 24 hours.'
        )
        break

    logger.info('safety_timer',
                f'Safety dead-man triggered (turn off if unused).')
    database.store('obs', {'deadman_keepalive': tick})

    tick += 1

    time.sleep(config.Timers.inactivity_timeout / 3)
