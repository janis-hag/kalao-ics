import time
from multiprocessing import Process, Queue

import numpy as np

from kalao import logger

from kalao.definitions.enums import ReturnCode


def get_name(func):
    return f'{func.func.__module__}.{func.func.__name__}'


def wrapper(log, func, queue):
    logger.info(log, f'Launching {get_name(func)} in background')
    ret = func()
    logger.info(log, f'{get_name(func)} returned {ret}')
    queue.put({get_name(func): ret})


def launch(log, func_list, timeout=np.inf, terminate_grace_time=5,
           kill_wait_time=1):
    processes = {}
    processes_terminated = {}
    processes_killed = {}
    processes_error = {}
    return_queue = Queue()
    returns = {}

    time_start = time.monotonic()

    # Launch all processes
    logger.info(log, f'Launching {len(func_list)} processes in background')
    for f in func_list:
        p = Process(target=wrapper, kwargs={
            'log': log,
            'func': f,
            'queue': return_queue
        })
        processes[get_name(f)] = p
        p.start()

    # Wait for all processes to finish
    logger.info(log, f'Waiting for processes in background to finish')
    timeout = time_start + timeout
    while time.monotonic() < timeout:
        alive = 0
        for f, p in processes.items():
            if p.is_alive():
                alive += 1

        if alive == 0:
            break

        time.sleep(1)

    # Terminate remaining ones
    for f, p in processes.items():
        if p.is_alive():
            logger.warn(log, f'Terminating process for {f}')
            processes_terminated[f] = p

            p.terminate()

    if len(processes_terminated) != 0:
        logger.info(log, f'Waiting for terminated processes to finish')
        time.sleep(terminate_grace_time)

    # Kill them if necessary
    for f, p in processes.items():
        if p.is_alive():
            logger.warn(log, f'Killing process for {f}')
            processes_killed[f] = p

            p.kill()

    if len(processes_killed) != 0:
        logger.info(log, f'Waiting for killed processes to finish')
        time.sleep(kill_wait_time)

    time_stop = time.monotonic()

    # Collecting return values of processes that finished
    while not return_queue.empty():
        returns.update(return_queue.get_nowait())

    for f, ret in returns.items():
        if ret != ReturnCode.OK:
            logger.error(log, f'{f} returned {ret}')
            processes_error[f] = ret

    logger.info(
        log,
        f'Background processes finished in {time_stop - time_start:.1f}s. {len(processes)} launched, {len(processes_terminated)} terminated, {len(processes_killed)} killed, {len(processes_error)} returned with error'
    )
