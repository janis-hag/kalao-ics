![KalAO](doc/logo/KalAO_def_200623.png?raw=true "Title")

![GitHub commit activity (branch)](https://img.shields.io/github/commit-activity/m/janis-hag/kalao-ics)
![GitHub language count](https://img.shields.io/github/languages/count/janis-hag/kalao-ics)

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
- Install configuration files symlinks:
    ```console
  kalaortc01:~>cd kalao-ics/kalao-config/
  kalaortc01:~/kalao-ics/kalao-config>bash ./install_symlinks.sh
    ```
- Start systemd serviced:
    ```console
  kalaortc01:~>cd kalao-ics/kalao-config/
  kalaortc01:~/kalao-ics/kalao-config>bash ./enable_systems.sh
    ```


## Configure telescope header content

Edit content of
- $THOME/config/ske_fits/generic_tele/kalao_descripteurs.ske
- $THOME/config/ske_fits/generic_synchro/kalao_descripteurs.ske

---
# AO calibration and testing

## Measuring the latency with mlat

- turn on the laser
- run mlat
- verifying output with gnuplot
- _cd ~/kalao-cacao/workdir/kalao-workdir/dmloop-workdir/fps.mlat-1.datadir_
- _gnuplot_
- gnuplot> _plot  "hardwlatency.dat" u 2:3_

## acqlin_zRM
## compsCM-1

## Sending turbulence on the DM

Start milk sessions by typing '_milk_'


- **Load turbulence file**
- milk> _loadfits "cube12_12_60000_v10mps_1ms_clean.fits" imc_
- **Open DM SHM channel**
- milk> _readshmim dm01disp04_
- **Send turbulence on DM channel at 1000 microsecond refresh rate**
- milk> _streamburst imc dm01disp04 1000_

Help for the commands is given with:

_milk> cmd? streamburst_
