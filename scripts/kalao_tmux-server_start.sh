#!/bin/bash

set -euo pipefail

source /home/kalao/.kalao_env
source /home/kalao/kalao-venv-3.11/bin/activate

cd /home/kalao/kalao-ics

# This service require "set-option exit-empty off" in .tmux.conf

/usr/bin/tmux start-server
