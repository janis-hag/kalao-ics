import time
from multiprocessing import Process, Queue

from kalao import logger

from kalao.definitions.enums import ReturnCode

import config


def launch(log, func_list):
    def get_name(f):
        return f'{f.func.__module__}.{f.func.__name__}'

    def wrapper(f, q):
        logger.info(log, f'Launching {get_name(f)} in background')
        ret = f()
        logger.info(log, f'{get_name(f)} returned {ret}')
        q.put({get_name(f): ret})

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
        p = Process(target=wrapper, kwargs={'f': f, 'q': return_queue})
        processes[get_name(f)] = p
        p.start()

    # Wait for all processes to finish
    logger.info(log, f'Waiting for processes in background to finish')
    timeout = time_start + config.SEQ.init_timeout
    while time.monotonic() < timeout:
        while not return_queue.empty():
            returns.update(return_queue.get_nowait())

        if len(returns) == len(func_list):
            break

    # Terminate remaining ones
    for f, p in processes.items():
        if p.is_alive():
            logger.warn(log, f'Terminating process for {f}')
            processes_terminated[f] = p

            p.terminate()

    if processes_terminated != 0:
        time.sleep(config.SEQ.init_terminate_grace_time)

    # Kill them if necessary
    for f, p in processes.items():
        if p.is_alive():
            logger.warn(log, f'Killing process for {f}')
            processes_killed[f] = p

            p.kill()

    if processes_killed != 0:
        time.sleep(config.SEQ.init_wait_kill)

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
