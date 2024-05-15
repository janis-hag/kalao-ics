#!/bin/bash

source /home/kalao/.kalao_env
source /home/kalao/kalao-venv-3.11/bin/activate

cd /home/kalao/kalao-ics

echo 'Shutdown initiated from shutdown.sh script' | systemd-cat -t shutdown.sh -p info

python -c 'from kalao.rtc import rtc; rtc.shutdown_sequence()' | systemd-cat -t shutdown.sh -p info
