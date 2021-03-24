#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from sys import path as SysPath
from os import path as OsPath
SysPath.append(OsPath.dirname(OsPath.abspath(OsPath.dirname(__file__))))

from threading import Thread
from multiprocessing import Process
from multiprocessing import Queue

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

# Multi-thread fonction: create array of object <function>
# Create a thread for each function and start the function
# Block until the end of each thread or timeout passed
# Then print return value and add return value to Queue object
def initBenchComponents(q):

	# array of object <function>
	init_foncs = [
		control.initialise,
		calib_unit.initialise,
		flip_mirror.initialise,
		shutter.initialise,
		tungsten.initialise,
		laser.initialise
	]

	threads = []
	returnInfo = []

	returnValue = 0

	# Create a thread for each function and set the thread's name to function's name
	for fonc in foncs:
		th = ThreadWithReturnValue(target = fonc)
		th.daemon = True
		th.start()
		th.setName(fonc.__name__)
		threads.append(th)

	# 'join' methode block until return of each thread or timeout expired
	# and return the function return value if timeout not expired
	# Set returnValue to 1 if timeout expired
	for th in threads:
		returnInfo.append( (th.getName(), th.join(timeout)) )
		if th.is_alive():
			print(th.getName(),"got timeout")
			returnValue = 1

	# Print each thread's name and the returned value of the thread
	# Set returnValue to 1 if a returned value is 1
	for r in returnInfo:
		print(r[0],":", r[1])
		if r[1] == 1:
			returnValue = 1

	q.put(returnValue)

def initialisation(nbTry, timeout):

	# READ CONFIG


	# Create a subprocess with a Queue object for return value
	# if returned value != 0, try 'nbTry' times
	for _ in range(nbTry):
		q = Queue()
		p = Process(target = initBenchComponents, arg = (q, timeout))
		p.start()
		p.join()

		if q.get() == 0:
			break


	# Start CACAO
