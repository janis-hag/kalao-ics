# This file was automatically generated by SWIG (http://www.swig.org).
# Version 4.0.1
#
# Do not make changes to this file unless you know what you are doing--modify
# the SWIG interface file instead.

from sys import version_info as _swig_python_version_info
if _swig_python_version_info < (2, 7, 0):
    raise RuntimeError("Python 2.7 or later required")

# Import the low-level C/C++ module
if __package__ or "." in __name__:
    from . import _pymod_libipc
else:
    import _pymod_libipc

try:
    import builtins as __builtin__
except ImportError:
    import __builtin__


def _swig_repr(self):
    try:
        strthis = "proxy of " + self.this.__repr__()
    except __builtin__.Exception:
        strthis = ""
    return "<%s.%s; %s >" % (
            self.__class__.__module__,
            self.__class__.__name__,
            strthis,
    )


def _swig_setattr_nondynamic_instance_variable(set):

    def set_instance_attr(self, name, value):
        if name == "thisown":
            self.this.own(value)
        elif name == "this":
            set(self, name, value)
        elif hasattr(self, name) and isinstance(getattr(type(self), name),
                                                property):
            set(self, name, value)
        else:
            raise AttributeError("You cannot add instance attributes to %s" %
                                 self)

    return set_instance_attr


def _swig_setattr_nondynamic_class_variable(set):

    def set_class_attr(cls, name, value):
        if hasattr(cls, name) and not isinstance(getattr(cls, name), property):
            set(cls, name, value)
        else:
            raise AttributeError("You cannot add class attributes to %s" % cls)

    return set_class_attr


def _swig_add_metaclass(metaclass):
    """Class decorator for adding a metaclass to a SWIG wrapped class - a slimmed down version of six.add_metaclass"""

    def wrapper(cls):
        return metaclass(cls.__name__, cls.__bases__, cls.__dict__.copy())

    return wrapper


class _SwigNonDynamicMeta(type):
    """Meta class to enforce nondynamic attributes (no new attributes) for a class"""
    __setattr__ = _swig_setattr_nondynamic_class_variable(type.__setattr__)


def select_key_semid_block(f_key):
    return _pymod_libipc.select_key_semid_block(f_key)


def init_semaphore():
    return _pymod_libipc.init_semaphore()


def init_block():
    return _pymod_libipc.init_block()


def select_semid_block(f_key, f_semid, f_block):
    return _pymod_libipc.select_semid_block(f_key, f_semid, f_block)


def init_ipc_remote_client(host, symb_name, rcmd, port):
    return _pymod_libipc.init_ipc_remote_client(host, symb_name, rcmd, port)


def select_for_remote(key, sd):
    return _pymod_libipc.select_for_remote(key, sd)


def init_ipc_remote_client_final():
    return _pymod_libipc.init_ipc_remote_client_final()


def init_remote_client(host, symb_name, rcmd, port, key):
    return _pymod_libipc.init_remote_client(host, symb_name, rcmd, port, key)


def shm_wait(timeout=0):
    return _pymod_libipc.shm_wait(timeout)


def shm_ack():
    return _pymod_libipc.shm_ack()


def shm_wack(timeout=0):
    return _pymod_libipc.shm_wack(timeout)


def shm_cont():
    return _pymod_libipc.shm_cont()


def shm_free():
    return _pymod_libipc.shm_free()


def set_sem(semnum, val):
    return _pymod_libipc.set_sem(semnum, val)


def get_val_sem(semnum):
    return _pymod_libipc.get_val_sem(semnum)


def get_ncount_sem(semnum):
    return _pymod_libipc.get_ncount_sem(semnum)


def get_zcount_sem(semnum):
    return _pymod_libipc.get_zcount_sem(semnum)


def get_cmd_sem_pid(semnum):
    return _pymod_libipc.get_cmd_sem_pid(semnum)


def ini_shm_kw():
    return _pymod_libipc.ini_shm_kw()


def put_shm_kw(key, content):
    return _pymod_libipc.put_shm_kw(key, content)


def get_shm_kw(key):
    return _pymod_libipc.get_shm_kw(key)


def get_shm_kw_n(i):
    return _pymod_libipc.get_shm_kw_n(i)


def put_shm_err(val):
    return _pymod_libipc.put_shm_err(val)


def get_shm_err(OutInt):
    return _pymod_libipc.get_shm_err(OutInt)


def put_shm_err_code(str):
    return _pymod_libipc.put_shm_err_code(str)


def get_shm_err_code(OutChar):
    return _pymod_libipc.get_shm_err_code(OutChar)


def put_shm_str_err(str):
    return _pymod_libipc.put_shm_str_err(str)


def get_shm_str_err(OutChar):
    return _pymod_libipc.get_shm_str_err(OutChar)


def put_shm_stat(val):
    return _pymod_libipc.put_shm_stat(val)


def get_shm_stat(OutInt):
    return _pymod_libipc.get_shm_stat(OutInt)


def get_shm_ackno(OutInt):
    return _pymod_libipc.get_shm_ackno(OutInt)


def send_signal(sig):
    return _pymod_libipc.send_signal(sig)


def get_shm_pid_client():
    return _pymod_libipc.get_shm_pid_client()


def get_shm_my_pid():
    return _pymod_libipc.get_shm_my_pid()


def get_srv_pid():
    return _pymod_libipc.get_srv_pid()


def get_shm_current_cmd(OutChar):
    return _pymod_libipc.get_shm_current_cmd(OutChar)


def send_cmd(command, timeouta, timeoutb):
    return _pymod_libipc.send_cmd(command, timeouta, timeoutb)
