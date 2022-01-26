![KalAO](doc/logo/KalAO_def_200623.png?raw=true "Title")

The KalAO Instrument Control Software
============


---

## Features
- PLC control through OPCUA
- Thorlabs Filterwheel control through TTYUSB

## TODO
- CACAO python control
- EULER Telescope inter-process communication
- Stand-alone filterwheel driver

---
# System deployment
- Pull into '~/kalao-ics/'


## Enabling services
- 'systemctl --user enable kalao_sequencer.service' 
- 'systemctl --user enable kalao_camera.service' 
- 'systemctl --user enable kalao_database_updater.service' 
- 'systemctl --user enable kalao_flask_gui.service'