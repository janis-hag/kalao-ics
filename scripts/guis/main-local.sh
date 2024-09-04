#!/bin/bash

set -euo pipefail

source /home/kalao/.kalao_env
source /home/kalao/kalao-venv-3.11/bin/activate

cd /home/kalao/kalao-ics

renice -n 19 $$

exec python /home/kalao/kalao-ics/kalao/guis/main.py
