#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : com_tools.py
# @Date : 2022-06-13-09-51
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg

"""
aocontrol.py is part of the KalAO Instrument Control Software
(KalAO-ICS).
"""

import subprocess
import os
import shutil
import time

import numpy as np

from CacaoProcessTools import fps, FPS_status
from pyMilk.interfacing.isio_shmlib import SHM

from kalao.cacao import telemetry


def set_modal_gain(mode, factor, stream_name='aol1_mgainfact'):
    """
    Function to change the gains of the AO control modes

    :param mode:
    :param factor:
    :param stream_name:
    :return:
    """
    exists, stream_path = telemetry.check_stream(stream_name)

    if exists:
        mgainfact_shm = SHM(stream_name)
        mgainfact_array = mgainfact_shm.get_data(check=False)

        mgainfact_array[mode] = factor

        mgainfact_shm.set_data(mgainfact_array.astype(mgainfact_shm.nptype))

        return 0

    else:
        return -1



def linear_low_pass_modal_gain_filter(cut_off, last_mode=None ,keep_existing_flat=False, stream_name='aol1_mgainfact'):
    """
    Applies a linear low-pass filter to the ao modal gains. The gain is flat until the cut_off mode where it starts
    decreasing down to zero for the last mode

    :param cut_off: mode at which the gain starts decreasing
    :param last_mode: modes higher than this mode are set to 0
    :param keep_existing_flat: keep the existing gain values instead of setting them to 1
    :param stream_name: name of the milk stream where the gain factor are stored
    :return:
    """

    exists, stream_path = telemetry.check_stream(stream_name)

    if exists:
        mgainfact_shm = SHM(stream_name)
        mgainfact_array = mgainfact_shm.get_data(check=False)


        if not keep_existing_flat:
            mgainfact_array = np.ones(len(mgainfact_array))

        if cut_off > len(mgainfact_array):
            # cut_off frequency has to be within the range of modes. If higher all values will be set to 1
            cut_off = len(mgainfact_array)

        if last_mode is None:
            last_mode = len(mgainfact_array)-1
        elif last_mode < cut_off:
            last_mode = cut_off
            mgainfact_array[last_mode:] = 0
        else:
            mgainfact_array[last_mode:] = 0

        if not cut_off ==  last_mode:
            #down = np.linspace(1, 0, len(mgainfact_array) - cut_off + 2 - (len(mgainfact_array) - last_mode) )[1:-1]
            down = np.linspace(1, 0, last_mode - cut_off + 2)[1:-1]
            mgainfact_array[cut_off:last_mode] = down


        mgainfact_shm.set_data(mgainfact_array.astype(mgainfact_shm.nptype))

        return 0

    else:
        return -1


##### Wait functions

def wait_loop(message, test):
    print(f"{message} ", end='', flush=True)
    while test():
        print(".", end='', flush=True)
        time.sleep(0.1)
    print(" DONE", flush=True)
    time.sleep(0.1)


def wait_stream(stream):
    wait_loop(f"Waiting {stream}", lambda: not os.path.exists(f"{os.environ['MILK_SHM_DIR']}/{stream}.im.shm"))


def wait_file(file):
    wait_loop(f"Waiting {file}", lambda: not os.path.exists(file))


##### Generic functions

def run_process(fpsname, waitend):
    print(f"########## {fpsname}")

    fpsi = fps(fpsname)
    print(f"########## md")
    md = fpsi.md()

    print(f"########## CONFrunning")
    # Check if configuration process is running
    if fpsi.CONFrunning != 1:
        raise Exception(f"CONF for {fpsname} should be running")

    print(f"########## CONFupdate")
    # Update conf
    fpsi.CONFupdate()

    print(f"########## conferrcnt")
    # Check the number of errors in the configuration
    if md.conferrcnt != 0:
        raise Exception(f"CONF for {fpsname} have {md.conferrcnt} errors")

    # If main process is running, do nothing, otherwise start it
    if fpsi.RUNrunning == 1:
        print(f"{fpsname} already running")
    else:
        pid = md.runpid
        fpsi.RUNstart()
        wait_loop(f"{fpsname} starting", lambda: md.runpid != pid)

    # Check if main process is correctly running
    if fpsi.RUNrunning == -1:
        raise Exception(f"Error while running {fpsname}")
    elif fpsi.RUNrunning == 0:
        raise Exception(f"{fpsname} did not start")

    # Wait the end of the main process if needed
    if waitend:
        wait_loop(f"Waiting end of {fpsname}", lambda: fpsi.RUNrunning == 1)

    return fpsi


#####

def clean():
    no = f"""
	n
	"""

    subprocess.run(["cacao-task-manager", "-C", "0", "ttmloop"], input=no, encoding='utf8')
    subprocess.run(["cacao-task-manager", "-C", "0", "dmloop"], input=no, encoding='utf8')
    subprocess.run(["pkill", "-f", "cacao"])
    subprocess.run(["pkill", "-f", "milk"])
    subprocess.run(["tmux", "kill-server"])
    subprocess.run([f"rm {os.environ['MILK_SHM_DIR']}/*"], shell=True)
    subprocess.run(["rm /dev/shm/sem..tmp.milk.*"], shell=True)
    subprocess.run(["rm step.aolaunch.*"], shell=True)


def init_loop(confname):
    subprocess.run(["cacao-task-manager", "-X", "4", confname])


def init_hardware(workdir):
    os.makedirs(workdir, exist_ok=True)

    cwd = os.getcwd()
    os.chdir(workdir)

    # TODO: os.environ NUVU_SDK_HARDWARE_CONCURRENCY=1

    subprocess.run(["milk-fpsinit", "-e", "cacao", "-C", "-f", "/home/kalao/KalAO/src/cacao/src/KalAO_BMC/fpslist.txt"])
    subprocess.run(
        ["milk-fpsinit", "-e", "cacao", "-C", "-f", "/home/kalao/KalAO/src/cacao/src/KalAO_Nuvu/fpslist.txt"])
    subprocess.run(
        ["milk-fpsinit", "-e", "cacao", "-C", "-f", "/home/kalao/KalAO/src/cacao/src/KalAO_SHWFS/fpslist.txt"])

    os.chdir(cwd)

    shutil.copytree("hardware-conf", workdir, dirs_exist_ok=True)


def configure_hardware(dm_conf, ttm_conf):
    fps_bmc = fps("bmc_display")
    fps_nuvu = fps("nuvu_acquire")
    fps_shwfs = fps("shwfs_process")

    fps_bmc.CONFstart()
    fps_nuvu.CONFstart()
    fps_shwfs.CONFstart()

    fps_bmc["bmc_display.DMin"] = f"dm{dm_conf['CACAO_DMINDEX']}disp"
    fps_bmc["bmc_display.TTMin"] = f"dm{ttm_conf['CACAO_DMINDEX']}disp"
    fps_bmc["bmc_display.ttm_tip_offset"] = 0.300
    fps_bmc["bmc_display.ttm_tilt_offset"] = -0.090

    fps_nuvu["nuvu_acquire.readoutmode"] = 4
    fps_nuvu["nuvu_acquire.emgain"] = 1
    fps_nuvu["nuvu_acquire.exposuretime"] = 0
    fps_nuvu["nuvu_acquire.autogain_params"] = "autogain_params.txt"

    fps_shwfs["shwfs_process.rawWFSin"] = "nuvu_stream"
    fps_shwfs["shwfs_process.spotcoords"] = "spots.txt"
    fps_shwfs["shwfs_process.outWFS"] = f"{dm_conf['CACAO_WFSSTREAM']}"


def start_hardware():
    run_process("bmc_display", False)

    run_process("nuvu_acquire", False)


def load_dm_flat(conf):
    wait_stream(f"dm{conf['CACAO_DMINDEX']}disp00")

    cwd = os.getcwd()
    os.chdir(f"{conf['CACAO_WORKDIR']}/hardware-workdir")  # TODO: use path.join()

    input = f"""
	loadfits "flat_dm.fits" dmflat
	readshmim dm{conf['CACAO_DMINDEX']}disp00
	cpsh dmflat dm{conf['CACAO_DMINDEX']}disp00
	exitCLI
	"""
    subprocess.run(["cacao"], input=input, encoding='utf8')

    os.chdir(cwd)


def start_shwfs():
    wait_stream(f"nuvu_stream")

    run_process("shwfs_process", False)


def do_calibration(conf):
    run_process(f"acquWFS-{conf['CACAO_LOOPNUMBER']}", False)

    fpsi = run_process(f"mlat-{conf['CACAO_LOOPNUMBER']}", True)
    latencyfr = fpsi[f"mlat-{conf['CACAO_LOOPNUMBER']}.out.latencyfr"]
    if (latencyfr > 3):
        raise Exception(f"Latency is too high ({latencyfr} frames)")

    run_process(f"acqlin_zRM-{conf['CACAO_LOOPNUMBER']}", True)

    run_process(f"acqlin_loRM-{conf['CACAO_LOOPNUMBER']}", True)

    run_process(f"compsCM-{conf['CACAO_LOOPNUMBER']}", True)

    cwd = os.getcwd()
    os.chdir(f"{conf['CACAO_WORKDIR']}/{conf['CACAO_LOOPWORKDIR']}")  # TODO: use path.join()

    input = f"""
	loadfits "fps.compsCM-{conf['CACAO_LOOPNUMBER']}.datadir/sCMat00.fits" sCMat00_{conf['CACAO_LOOPNUMBER']}
	cpsh sCMat00_{conf['CACAO_LOOPNUMBER']} aol{conf['CACAO_LOOPNUMBER']}_CMat
	exitCLI
	"""
    subprocess.run(["cacao"], input=input, encoding='utf8')

    os.chdir(cwd)

    run_process("compsCM-{conf['CACAO_LOOPNUMBER']}", False)


def close_loop():
    pass


def check_loop():
    # TODO check if loop is running. If loop broken return -1
    pass
