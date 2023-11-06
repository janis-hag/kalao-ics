#!/bin/bash

source /home/kalao/.kalao_env
source /home/kalao/kalao-venv/bin/activate

mount -a

cset set -c 5 nuvu_cpuset
cset set -c 6 bmc_cpuset
cset set -c 7 mfilt_dm_cpuset

cset proc -k --force -m "$(pgrep irq/16-edt)" nuvu_cpuset
