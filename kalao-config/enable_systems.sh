#!/usr/bin/env bash

systemctl --user enable kalao_sequencer.service
systemctl --user enable kalao_camera.service
systemctl --user enable kalao_database-updater.service
systemctl --user enable kalao_flask-gui.service
systemctl --user enable kalao_gop_server.service
systemctl --user enable kalao_safety-watchdog.service
systemctl --user enable kalao_pump-watchdog.service

systemctl --user start kalao_sequencer.service
systemctl --user start kalao_camera.service
systemctl --user start kalao_database-updater.service
systemctl --user start kalao_flask-gui.service
systemctl --user start kalao_gop_server.service
systemctl --user start kalao_safety-watchdog.service
systemctl --user start kalao_pump-watchdog.service
