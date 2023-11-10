#!/usr/bin/env bash
set -x

# Enabling/installing services
systemctl --user enable kalao_cacao.service
systemctl --user enable kalao_sequencer.service
systemctl --user enable kalao_camera.service
systemctl --user enable kalao_flask-gui.service
systemctl --user enable kalao_gop_server.service
systemctl --user enable kalao_database-timer.service
systemctl --user enable kalao_safety-timer.service
systemctl --user enable kalao_pump-timer.service
systemctl --user enable kalao_loop-timer.service

# Starting services
systemctl --user start kalao_cacao.service
systemctl --user start kalao_sequencer.service
systemctl --user start kalao_camera.service
systemctl --user start kalao_flask-gui.service
systemctl --user start kalao_gop_server.service
systemctl --user start kalao_database-timer.service
systemctl --user start kalao_safety-timer.service
systemctl --user start kalao_pump-timer.service
systemctl --user start kalao_loop-timer.service

# Printing out status
# systemctl --user status

# Install system services
sudo ln -s /home/kalao/kalao-ics/kalao-config/kalao_system-setup.service /etc/systemd/system/
sudo systemctl enable kalao_system-setup.service
sudo systemctl start kalao_system-setup.service

set +x
