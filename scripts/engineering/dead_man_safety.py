import time

from kalao.utils import kalao_time
from sequencer import system

import kalao_config as config

start_time = kalao_time.now()

while True:
    ellapsed_time = (kalao_time.now() - start_time).total_seconds()

    if ellapsed_time > 24 * 60 * 60:
        print("Killing safety dead-man as it has been running since more than 24 hours.")
        break

    system.print_and_log("Safety dead-man triggered (turn off if unused).")
    time.sleep(config.Timers.inactivity_timeout / 3)
