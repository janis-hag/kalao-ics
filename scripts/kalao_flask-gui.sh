#!/bin/bash

source /home/kalao/kalao-venv/bin/activate

cd /home/kalao/kalao-ics/gui_flask

MILK_SHM_DIR='/tmp/milk' waitress-serve --call 'KalAO_flask:create_app'
