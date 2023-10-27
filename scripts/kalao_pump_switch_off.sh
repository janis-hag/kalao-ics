#!/bin/bash

source /home/kalao/.kalao_env
source /home/kalao/kalao-venv/bin/activate

cd /home/kalao/kalao-ics

python -c 'from kalao.plc import temperature_control; temperature_control.pump_off()'
