import time

from sequencer import system

import kalao_config as config

while True:
    system.print_and_log("Safety dead-man triggered (turn off if unused).")
    time.sleep(config.Watchdog.inactivity_timeout/3)