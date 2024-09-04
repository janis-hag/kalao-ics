import time
from datetime import datetime, timezone

from kalao.ics import database, logger

import config

start_time = datetime.now(timezone.utc)
tick = 0

while True:
    ellapsed_time = (datetime.now(timezone.utc) - start_time).total_seconds()

    if ellapsed_time > 86400:
        logger.info(
            'hardware_timer',
            'Killing inactivity dead-man as it has been running since more than 24 hours.'
        )
        break

    logger.info('hardware_timer',
                'Inactivity dead-man triggered (turn off if unused).')
    database.store('obs', {'deadman_keepalive': tick})

    tick += 1

    time.sleep(config.Hardware.inactivity_timeout / 3)
