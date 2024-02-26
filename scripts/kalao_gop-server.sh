#!/bin/bash

source /home/kalao/.kalao_env
source /home/kalao/kalao-venv-3.11/bin/activate

cd /home/kalao/kalao-ics

python /home/kalao/kalao-ics/tcs_communication/KalAO_GOP_server.py
