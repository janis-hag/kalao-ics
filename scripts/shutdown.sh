#!/bin/bash

source /home/kalao/.kalao_env
source /home/kalao/kalao-venv-3.11/bin/activate

cd /home/kalao/kalao-ics

journalctl -n0 -f -t shutdown.sh &
pid_journal=$!

sleep 1

systemd-cat -t shutdown.sh -p info echo 'Shutdown initiated from shutdown.sh script'
systemd-cat -t shutdown.sh -p info python -c 'from kalao.rtc import rtc; rtc.shutdown_sequence()' &
pid_script=$!

wait $pid_script
returncode_script=$?

kill $pid_journal

exit $returncode_script