#!/usr/bin/env bash

set -euo pipefail

set -x

# Install system services
cp /home/kalao/kalao-ics/kalao-config/kalao_system-setup.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable kalao_system-setup.service
systemctl start kalao_system-setup.service

# Allow kalao user to reboot or power off

# TODO: change to /etc/polkit-1/rules.d when updating system

cat << 'EOF' > /etc/polkit-1/localauthority/50-local.d/50-kalao.pkla
[KalAO]
Identity=unix-user:kalao
Action=org.freedesktop.login1.*
ResultAny=yes
ResultInactive=yes
ResultActive=yes
EOF

set +x
