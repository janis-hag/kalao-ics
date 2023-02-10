#!/usr/bin/env bash

systemctl --user enable kalao_sequencer.service
systemctl --user enable kalao_camera.service
systemctl --user enable kalao_database_updater.service
systemctl --user enable kalao_flask_gui.service
systemctl --user enable kalao_gop_server.service
systemctl --user enable kalao_safety-watchdog.service
systemctl --user enable kalao_pump-watchdog.service
