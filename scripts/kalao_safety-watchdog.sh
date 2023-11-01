#!/bin/bash

source /home/kalao/.kalao_env
source /home/kalao/kalao-venv/bin/activate

cd /home/kalao/kalao-ics/kalao/utils

python /home/kalao/kalao-ics/kalao/watchdogs/safety.py
