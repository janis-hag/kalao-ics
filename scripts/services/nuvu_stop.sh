#!/bin/bash

set -euo pipefail

source /home/kalao/.kalao_env
source /home/kalao/kalao-venv-3.11/bin/activate

cd /home/kalao/kalao-ics

python -c 'from kalao.hardware import wfs; exit(wfs.stop())'
