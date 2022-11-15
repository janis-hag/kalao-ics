#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Nathanaël Restori
"""

import json
import subprocess
import os
import shutil
import time
import sys

from CacaoProcessTools import fps, FPS_status


def source_conf(confname):
	vars = {}

	workdir = open(f"{confname}-conf/WORKDIR", 'r').read().splitlines()[0]
	loopname = open(f"{confname}-conf/LOOPNAME", 'r').read().splitlines()[0]

	file_to_source = f"{confname}-conf/cacaovars.{loopname}.bash"

	command = f"env -i bash -c 'set -a && source {file_to_source} && env'"

	# Get all the vars in "file_to_source"
	for line in subprocess.getoutput(command).split("\n"):
		key, value = line.split("=", 1)
		vars[key]= value

	vars["CACAO_WORKDIR"] = workdir
	vars["CACAO_LOOPNAME"] = loopname

	return vars

##### Wait functions

def wait_loop(message, test):
	print(f"{message} ", end='', flush=True)
	while test():
		print(".", end='', flush=True)
		time.sleep(0.1)
	print(" DONE", flush=True)
	time.sleep(0.1)


def wait_stream(stream):
	wait_loop(f"Waiting {stream}", lambda : not os.path.exists(f"{os.environ['MILK_SHM_DIR']}/{stream}.im.shm"))


def wait_file(file):
	wait_loop(f"Waiting {file}", lambda : not os.path.exists(file))

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
		wait_loop(f"{fpsname} starting", lambda : md.runpid != pid)

	# Check if main process is correctly running
	if fpsi.RUNrunning == -1:
		raise Exception(f"Error while running {fpsname}")
	elif fpsi.RUNrunning == 0:
		raise Exception(f"{fpsname} did not start")

	# Wait the end of the main process if needed
	if waitend:
		wait_loop(f"Waiting end of {fpsname}", lambda : fpsi.RUNrunning == 1)

	return fpsi

#####

def clean():
	no = f"""
	n
	"""

	subprocess.run(["cacao-task-manager", "-C", "0", "ttmloop"], input=no, encoding='utf8')
	subprocess.run(["cacao-task-manager", "-C", "0", "dmloop"],  input=no, encoding='utf8')
	subprocess.run(["cacao-task-manager", "-C", "0", "kalaohardware"],  input=no, encoding='utf8')
	subprocess.run(["pkill", "-f", "cacao"])
	subprocess.run(["pkill", "-f", "milk"])
	subprocess.run(["tmux", "kill-server"])
	subprocess.run([f"rm {os.environ['MILK_SHM_DIR']}/*"], shell=True)
	subprocess.run(["rm /dev/shm/sem..tmp.milk.*"], shell=True)
	subprocess.run(["rm step.aolaunch.*"], shell=True)
	subprocess.run(["rm -r .*cacaotaskmanager-log"], shell=True)

def init_loop(confname):
	subprocess.run(["cacao-task-manager", "-X", "4", confname])


def init_hardware(workdir):
	os.makedirs(workdir, exist_ok=True)

	cwd = os.getcwd()
	os.chdir(workdir)

	subprocess.run(["milk-fpsinit", "-e", "cacao", "-C", "-f", "/home/kalao/KalAO/src/cacao/src/KalAO_BMC/fpslist.txt"])
	subprocess.run(["milk-fpsinit", "-e", "cacao", "-C", "-f", "/home/kalao/KalAO/src/cacao/src/KalAO_Nuvu/fpslist.txt"])
	subprocess.run(["milk-fpsinit", "-e", "cacao", "-C", "-f", "/home/kalao/KalAO/src/cacao/src/KalAO_SHWFS/fpslist.txt"])

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
	fps_nuvu["nuvu_acquire.exposuretime"] =  0
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
	os.chdir(f"{conf['CACAO_WORKDIR']}/hardware-workdir") #TODO: use path.join()

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
	if(latencyfr > 3):
		raise Exception(f"Latency is too high ({latencyfr} frames)")

	run_process(f"acqlin_zRM-{conf['CACAO_LOOPNUMBER']}", True)

	run_process(f"acqlin_loRM-{conf['CACAO_LOOPNUMBER']}", True)

	run_process(f"compsCM-{conf['CACAO_LOOPNUMBER']}", True)

	cwd = os.getcwd()
	os.chdir(f"{conf['CACAO_WORKDIR']}/{conf['CACAO_LOOPWORKDIR']}") #TODO: use path.join()

	input = f"""
	loadfits "fps.compsCM-{conf['CACAO_LOOPNUMBER']}.datadir/sCMat00.fits" sCMat00_{conf['CACAO_LOOPNUMBER']}
	cpsh sCMat00_{conf['CACAO_LOOPNUMBER']} aol{conf['CACAO_LOOPNUMBER']}_CMat
	exitCLI
	"""
	subprocess.run(["cacao"], input=input, encoding='utf8')

	os.chdir(cwd)

	run_process("compsCM-{conf['CACAO_LOOPNUMBER']}", False)

def close_loop():
	return 0

def check_loop():
	# TODO check if loop is running. If loop broken return -1
	pass

#################################

if __name__ == "__main__":
	if len(sys.argv) != 2:
		print("This script need one argument")
		exit(1)

	if sys.argv[1] == "clean":
		clean()
	elif sys.argv[1] == "launch":
		dm_conf = source_conf("dmloop")
		ttm_conf = source_conf("ttmloop")

		init_hardware(f"{dm_conf['CACAO_WORKDIR']}/hardware-workdir")
		init_loop("dmloop")
		init_loop("ttmloop")
		init_loop("kalaohardware")

		#TODO: remove when Olivier fix cacaotask-STARTDMCOMB and uncomment STARTDMCOMB in tasklist.txt
		fps_dmcomb01 = fps("DMcomb-01")
		fps_dmcomb01.RUNstart()
		fps_dmcomb01.CONFupdate()
		fps_dmcomb02 = fps("DMcomb-02")
		fps_dmcomb02.RUNstart()
		fps_dmcomb02.CONFupdate()

		configure_hardware(dm_conf, ttm_conf)
		start_hardware()
		load_dm_flat(dm_conf)
		start_shwfs()

		do_calibration(dm_conf)
	elif sys.argv[1] == "bmc":
		run_process("bmc_display", False)
	elif sys.argv[1] == "nuvu":
		run_process("nuvu_acquire", False)
	elif sys.argv[1] == "mlat":
		run_process("mlat-1", True)
	else:
		print("Unknown mode")
