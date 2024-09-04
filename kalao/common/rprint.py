from threading import RLock

lock = RLock()


def rprint(*args, **kwargs):
    with lock:
        print(*args, **kwargs)
