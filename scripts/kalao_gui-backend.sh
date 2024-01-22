#!/bin/bash

source /home/kalao/.kalao_env
source /home/kalao/kalao-venv-3.11/bin/activate

cd /home/kalao/kalao-ics

python /home/kalao/kalao-ics/guis/backends/http_server.py
