import time

from kalao import logger
from kalao.utils import kalao_time

import config

start_time = kalao_time.now()

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
    time.sleep(config.Timers.inactivity_timeout / 3)
