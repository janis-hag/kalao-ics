import time

from kalao.utils import database, kalao_time

import config

start_time = kalao_time.now()

while True:
    ellapsed_time = (kalao_time.now() - start_time).total_seconds()

    if ellapsed_time > 86400:
        database.store(
            'obs', {
                'safety_timer_log':
                    'Killing safety dead-man as it has been running since more than 24 hours.'
            })
        break

    database.store('obs', {
        'safety_timer_log': 'Safety dead-man triggered (turn off if unused).'
    })
    time.sleep(config.Timers.inactivity_timeout / 3)
