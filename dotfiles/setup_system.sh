#!/usr/bin/env bash

set -euo pipefail

set -x

# Install system services
cp /home/kalao/kalao-ics/dotfiles/kalao_system-setup.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable kalao_system-setup.service
systemctl start kalao_system-setup.service

# Allow kalao user to change CPU scheduling and niceness

mkdir -p /etc/systemd/system/user@1000.service.d

cat << 'EOF' > /etc/systemd/system/user@1000.service.d/override.conf
[Service]
AmbientCapabilities=CAP_SYS_NICE
EOF

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

#cat << 'EOF' > /etc/polkit-1/rules.d/50-kalao.rules
#polkit.addRule(function(action, subject) {
#    if (action.id.match("^org.freedesktop.login1.*") && subject.user == "kalao") {
#        return polkit.Result.YES;
#    }
#});
#EOF

set +x
