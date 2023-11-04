#!/bin/bash

source /home/kalao/.kalao_env
source /home/kalao/kalao-venv/bin/activate

base_folder="/gls/data/raw/kalao"
last_folder=$(ls -1 "${base_folder}" | tail -n1)
last_file=$(ls -1 "${base_folder}/${last_folder}" | tail -n1)

file="${base_folder}/${last_folder}/${last_file}"

echo "Opening ${file} ..."

ds9 "$file"
