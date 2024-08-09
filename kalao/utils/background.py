import multiprocessing
import time
from multiprocessing import Process, Queue
from typing import Callable

import numpy as np

from kalao import logger

from kalao.definitions.enums import ReturnCode


def _get_name(func: Callable) -> str:
    if hasattr(func, '__name__'):
        return f'{func.__module__}.{func.__name__}'
    else:
        return _get_name(func.func)


def _wrapper(log: str, func: Callable, queue: Queue) -> None:
    logger.info(log, f'Launching {_get_name(func)} in background')

    try:
        ret = func()
    except Exception as e:
        logger.error(log,
                     f'Exception occurred during {_get_name(func)} execution')
        logger.exception(log, e)
        ret = ReturnCode.EXCEPTION
    else:
        if isinstance(ret, ReturnCode):
            message = f'{_get_name(func)} returned {ret.value} ({ret.name})'
            if ret != ReturnCode.OK:
                logger.warn(log, message)
            else:
                logger.info(log, message)
        else:
            logger.info(log, f'{_get_name(func)} returned {ret}')
    queue.put({_get_name(func): ret})


def launch(log: str, func_list: list[Callable], timeout: float = np.inf,
           terminate_grace_time: float = 5, kill_wait_time: float = 1) -> None:
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
        p = Process(target=_wrapper, kwargs={
            'log': log,
            'func': f,
            'queue': return_queue
        })
        processes[_get_name(f)] = p
        p.start()

    # Wait for all processes to finish
    logger.info(log, 'Waiting for processes in background to finish')
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
        logger.info(log, 'Waiting for terminated processes to finish')
        time.sleep(terminate_grace_time)

    # Kill them if necessary
    for f, p in processes.items():
        if p.is_alive():
            logger.warn(log, f'Killing process for {f}')
            processes_killed[f] = p

            p.kill()

    if len(processes_killed) != 0:
        logger.info(log, 'Waiting for killed processes to finish')
        time.sleep(kill_wait_time)

    time_stop = time.monotonic()

    # Collecting return values of processes that finished
    while not return_queue.empty():
        returns.update(return_queue.get_nowait())

    for f, ret in returns.items():
        if ret != ReturnCode.OK:
            processes_error[f] = ret

    # Avoid zombie processes
    multiprocessing.active_children()

    logger.info(
        log,
        f'Background processes finished in {time_stop - time_start:.1f}s. {len(processes)} launched, {len(processes_terminated)} terminated, {len(processes_killed)} killed, {len(processes_error)} returned with error'
    )
