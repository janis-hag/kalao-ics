#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from threading import Thread

from kalao.plc import shutter
from kalao.plc import calib_unit
from kalao.plc import flip_mirror
from kalao.plc import laser
from kalao.plc import tungsten
from kalao.fli import control

# Thread subclass that allows you to retrieve a return value
# **https://stackoverflow.com/questions/6893968/how-to-get-the-return-value-from-a-thread-in-python**
class ThreadWithReturnValue(Thread):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None
    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)
    def join(self, *args):
        Thread.join(self, *args)
        return self._return

# Multi-thread fonction: take array of object <function>
# Create a thread for each function and start the function
# Block until the end of each thread and print return value.
def multi_threading(foncs, timeout = None):
	threads = []
	returnInfo = []

	for fonc in foncs:
		th = ThreadWithReturnValue(target = fonc)
		th.start()
		th.setName(fonc.__name__)
		threads.append(th)

	for th in threads:
		returnInfo.append( (th.getName(), th.join(timeout)) )

	for r in returnInfo:
		print(r[0],":", r[1])


# Define each init process of some composants
# Start them in multi-thread
def initialisation():

	def init_FLI_cam():
		control.initialise()

	def check_PLC_init_status():
		foncs = [
			calib_unit.initialise,
			flip_mirror.initialise,
			shutter.initialise
		]

		multi_threading(foncs)

	def init_CACAO():
		pass

	def init_Shutter():
		shutter.initialise()

	def init_Tungsten():
		tungsten.initialise()


	init_foncs = [
		init_FLI_cam,
		check_PLC_init_status,
		init_CACAO,
		init_Shutter,
		init_Tungsten
	]

	multi_threading(init_foncs)
