#!/bin/bash

source /home/kalao/.kalao_env
source /home/kalao/kalao-venv/bin/activate

cd /home/kalao/kalao-ics

python -c 'from kalao.cacao import aocontrol; aocontrol.stop_wfs()'
