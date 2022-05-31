#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Filename : system.py
# @Date : 2021-08-16-13-33
# @Project: KalAO-ICS
# @AUTHOR : Janis Hagelberg

"""
seq_init.py is part of the KalAO Instrument Control Software
(KalAO-ICS).
"""

from sys import path as SysPath
from os  import path as OsPath
# methode dirname return parent directory and methode abspath return absolut path
SysPath.append(OsPath.dirname(OsPath.abspath(OsPath.dirname(__file__))))

from threading          import Thread
from multiprocessing    import Process, Queue
from configparser       import ConfigParser

from pathlib import Path
import os

from kalao.plc import shutter
from kalao.plc import calib_unit
from kalao.plc import flip_mirror
from kalao.plc import laser
from kalao.plc import tungsten
from kalao.fli import camera

from sequencer import system

class ThreadWithReturnValue(Thread):
    """
    Thread subclass that allows you to retrieve a return value
    https://stackoverflow.com/questions/6893968/how-to-get-the-return-value-from-a-thread-in-python
    """
    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None
    def run(self):
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
    """
    Create a thread for each function in 'init_foncs' list and start it.
    Then, block for each thread until his end.
    If a thread got an error, add name's function to 'q' parameter.

    :param q: Queue object for mutlithread communication
    :param init_foncs: list of function object
    :return:
    """

    threads = []

    # Create a thread for each function and set the thread's name to function's name
    for fonc in init_foncs:
        th = ThreadWithReturnValue(target = fonc)
        th.daemon = True

        name = fonc.__module__.split(".")[-1] + "." + fonc.__name__
        system.print_and_log(str(name)+" started..")
        # name last_module_name.func_name (ex: control.initialise)

        th.start()
        th.setName(name)
        threads.append(th)

    # 'join' methode block until return of each thread or timeout expired
    # and return the function return value if timeout not expired
    # Set returnValue to 1 if timeout expired
    for th in threads:
        rValue = th.join()
        if rValue != 0:
            system.print_and_log("ERROR: "+str(th.getName())+" return "+str(rValue))
            q.put(th.getName())
            # add func's name who got an error to Queue object for retry
        else:
            system.print_and_log(str(th.getName())+" initialised.")


def startThread(q, timeout, init_foncs):
    """
    Create a thread and block until its end or until the allowed time is exceeded.


    :param q: Queue object for mutlithread communication
    :param timeout: int corresponding to the number of seconds allowed for the initialization
    :param init_foncs: list of function object
    :return:
    """
    th = ThreadWithReturnValue(target = initBenchComponents, args = (q, init_foncs))
    th.daemon = True
    print("Subthreads started..")
    th.start()
    th.join(timeout)

    # if subthread still alive after timeout second, add flag 1 to Queue object
    # and end the process, killing the subtread still alive
    if th.is_alive():
        print("Initialisation got timeout")
        q.put(1)
    else:
        print("All subthreads returned")


def startProcess(startThread, q, timeout, init_foncs):
    """
    Create a sub-process and block it until the end.
    This is done in order to kill all sub-threads if a timeout occurs

    :param startThread:
    :param q:
    :param timeout:
    :param init_foncs:
    :return:
    """

    p = Process(target = startThread, args = (q, timeout, init_foncs))
    print("Subprocess started..")
    p.start()
    p.join()
    print("Subprocess OK")


def initialisation():
    """
    Read the configuration file.
    Create a sub-process with initialisation function.

    :return:
    """

    system.print_and_log('Starting initalisation')
    # read config file

    config_path = os.path.join(Path(os.path.abspath(__file__)).parents[1], 'kalao.config')

    #Verify that config file exists
    if not Path(config_path).is_file():
        system.print_and_log('kalao.config file not found at: '+config_path)
        return -1

    parser = ConfigParser()
    parser.read(config_path)

    nbTry   = parser.getint('PLC','InitNbTry')
    timeout = parser.getint('PLC','InitTimeout')

    # dict where keys is string name of object <function> and values is object <function>
    init_dict = {
        "system.initialise_services"     : system.initialise_services,
        "control.initialise"    : camera.initialise,
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

    for t in range(1,nbTry):
        value = 0
        error_foncs = []

        while not q.empty():
            value = q.get()

            # if value egal 1 then a timeout happened
            # clear queue object and try again
            if value == 1:
                while not q.empty():
                    q.get()
                print(t,"retry..")
                startProcess(startThread, q, timeout, init_foncs)
                break
            else:
                # add func's name who got an error to a list for retry
                error_foncs.append(init_dict[value])

        if value == 1:
            continue
        elif error_foncs == []:
            return 0
        else:
            # retry only func who got an error
            startProcess(startThread, q, timeout, error_foncs)

    return 1

    # Start CACAO here ----

if __name__ == "__main__":
    initialisation()
