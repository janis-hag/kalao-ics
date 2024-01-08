#!/bin/bash

source /home/kalao/.kalao_env
source /home/kalao/kalao-venv-3.11/bin/activate

cd /home/kalao/kalao-ics

python -c 'from kalao.cacao import aocontrol; aocontrol.start_wfs()'
