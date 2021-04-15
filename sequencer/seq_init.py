#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from sys import path as SysPath
from os  import path as OsPath
# methode dirname return parent directory and methode abspath return absolut path
SysPath.append(OsPath.dirname(OsPath.abspath(OsPath.dirname(__file__))))

from threading          import Thread
from multiprocessing    import Process, Queue
from configparser       import ConfigParser

from kalao.plc import shutter
from kalao.plc import calib_unit
from kalao.plc import flip_mirror
from kalao.plc import laser
from kalao.plc import tungsten
from kalao.fli import control

import seq_server
import seq_command

# Thread subclass that allows you to retrieve a return value
# **https://stackoverflow.com/questions/6893968/how-to-get-the-return-value-from-a-thread-in-python**
class ThreadWithReturnValue(Thread):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None
    def run(self):watch?v=AQ7-qKQMce4
        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)
    def join(self, *args):
        Thread.join(self, *args)
        return self._return

# Multi-thread fonction: take array of func objects
# Create a thread for each function and start the function
# 'join' methode block until the end of each thread
# Then print return value and add return value to Queue object
# And add name of func who returned error to Queue object
def initBenchComponents(q, init_foncs):

    threads = []

    # Create a thread for each function and set the thread's name to function's name
    for fonc in init_foncs:
        th = ThreadWithReturnValue(target = fonc)
        th.daemon = True
        th.start()
        th.setName(fonc.__name__)
        threads.append(th)

    # 'join' methode block until return of each thread or timeout expired
    # and return the function return value if timeout not expired
    # Set returnValue to 1 if timeout expired
    for th in threads:
        rValue = th.join()
        if rValue != 0:
            print("Error:",th.getName(), "return", rValue)
            q.put(th.getName())

def startThread(q, timeout, init_foncs):
    th = ThreadWithReturnValue(target = initBenchComponents, args = (q, init_foncs))
    th.daemon = True
    th.start()
    th.join(timeout)
    if th.is_alive():
        print("Initialisation got timeout")
        q.put(1)

def startProcess(startThread, q, timeout, init_foncs):
    p = Process(target = startThread, args = (q, timeout, init_foncs))
    p.start()
    p.join()

def initialisation():

    # Read config file and create a dict for each section where keys is parameter
    parser = ConfigParser()
    parser.read('../kalao.config')

    nbTry   = parser.getint('PLC','InitNbTry')
    timeout = parser.getint('PLC','InitTimeout')

    # dict where keys is string name of object <function> and values is object <function>
    init_dict = {
        "control.initialise"    : control.initialise,
        "calib_unit.initialise" : calib_unit.initialise,
        "flip_mirror.initialise": flip_mirror.initialise,
        "shutter.initialise"    : shutter.initialise,
        "tungsten.initialise"   : tungsten.initialise,
        "laser.initialise"      : laser.initialise
    }

    # array of object <function>
    init_foncs = list(init_dict.values())

    # Create a subprocess with a Queue object for return value
    # if returned value != 0, try 'nbTry' times
    q = Queue()
    startProcess(startThread, q, timeout, init_foncs)

    for _ in range(nbTry):
        value = 0
        error_foncs = []

        while not q.empty():
            value = q.get()

            # if value egal 1 then a timeout happened
            # clear queue object and try again
            if value == 1:
                while not q.empty():
                    q.get()
                startProcess(startThread, q, timeout, init_foncs)
                break
            else:
                error_foncs.append(init_dict[value])

        if value == 1:
            continue
        elif error_foncs == []:
            return 0
        else:
            startProcess(startThread, q, timeout, error_foncs)

    return 1


    # Start CACAO here ----
