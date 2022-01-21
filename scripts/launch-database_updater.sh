#!/bin/bash

source /home/kalao/kalao-venv/bin/activate
source /home/kalao/kalao-config/_bash_aliases

cd /home/kalao/kalao-ics/kalao/utils

python3 /home/kalao/kalao-ics/kalao/utils/database_updater.py
