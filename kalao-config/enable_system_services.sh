#!/usr/bin/env bash
set -x

# Install system services
sudo ln -s /home/kalao/kalao-ics/kalao-config/kalao_system-setup.service /etc/systemd/system/
sudo systemctl enable kalao_system-setup.service
sudo systemctl start kalao_system-setup.service

set +x
