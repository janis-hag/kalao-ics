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
- _systemctl --user enable kalao_sequencer.service_ 
- _systemctl --user enable kalao_camera.service_
- _systemctl --user enable kalao_database_updater.service_ 
- _systemctl --user enable kalao_flask_gui.service_

---
# AO calibration and testing

## Measuring the latency with mlat

- turn on the laser
- run mlat
- verifying output with gnuplot

## acqlin_zRM
## compsCM-1

## Sending turbulence on the DM

Start milk sessions by typing '_milk_'


- **Load turbulence file**
- milk> _loadfits "cube12_12_60000_v10mps_1ms.fits" imc_
- **Open DM SHM channel** 
- milk> _readshmim dm01disp04_
- **Send turbulence on DM channel at 1000 microsecond refresh rate**
- milk> _streamburst imc dm01disp04 1000_

Help for the commands is given with:

_milk> cmd? streamburst_
