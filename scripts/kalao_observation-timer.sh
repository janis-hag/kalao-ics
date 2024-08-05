#!/bin/bash



source /home/kalao/.kalao_env
source /home/kalao/kalao-venv-3.11/bin/activate

cd /home/kalao/kalao-ics

exec python /home/kalao/kalao-ics/kalao/timers/observation.py
