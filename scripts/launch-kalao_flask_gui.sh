#!/bin/bash

source /home/kalao/kalao-venv/bin/activate

cd /home/kalao/kalao-ics/gui_flask

waitress-serve --call 'KalAO_flask:create_app'
