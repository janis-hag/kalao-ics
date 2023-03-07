#!/bin/bash

source /home/kalao/kalao-venv/bin/activate

cd /home/kalao/kalao-ics/gui_flask

#MILK_SHM_DIR='/tmp/milk' gunicorn -w 4 -b 0.0.0.0:8080 "KalAO_flask:create_app()"
MILK_SHM_DIR='/tmp/milk' nice -20 python KalAO_flask.py
