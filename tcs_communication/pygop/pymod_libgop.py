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
    from . import _pymod_libgop
else:
    import _pymod_libgop

try:
    import builtins as __builtin__
except ImportError:
    import __builtin__

def _swig_repr(self):
    try:
        strthis = "proxy of " + self.this.__repr__()
    except __builtin__.Exception:
        strthis = ""
    return "<%s.%s; %s >" % (self.__class__.__module__, self.__class__.__name__, strthis,)


def _swig_setattr_nondynamic_instance_variable(set):
    def set_instance_attr(self, name, value):
        if name == "thisown":
            self.this.own(value)
        elif name == "this":
            set(self, name, value)
        elif hasattr(self, name) and isinstance(getattr(type(self), name), property):
            set(self, name, value)
        else:
            raise AttributeError("You cannot add instance attributes to %s" % self)
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



def gop_get_error_str():
    return _pymod_libgop.gop_get_error_str()

def gop_process_registration(arg1, arg2, arg3, arg4, arg5):
    return _pymod_libgop.gop_process_registration(arg1, arg2, arg3, arg4, arg5)

def gop_alloc_connect_structure():
    return _pymod_libgop.gop_alloc_connect_structure()

def gop_connection(arg1):
    return _pymod_libgop.gop_connection(arg1)

def gop_init_connection(arg1):
    return _pymod_libgop.gop_init_connection(arg1)

def gop_accept_connection(arg1):
    return _pymod_libgop.gop_accept_connection(arg1)

def gop_init_server_socket(arg1, arg2, arg3, arg4, arg5, arg6):
    return _pymod_libgop.gop_init_server_socket(arg1, arg2, arg3, arg4, arg5, arg6)

def gop_init_client_socket(arg1, arg2, arg3, arg4, arg5, arg6, arg7):
    return _pymod_libgop.gop_init_client_socket(arg1, arg2, arg3, arg4, arg5, arg6, arg7)

def gop_init_server_socket_unix(arg1, arg2, arg3, arg4, arg5, arg6):
    return _pymod_libgop.gop_init_server_socket_unix(arg1, arg2, arg3, arg4, arg5, arg6)

def gop_init_client_socket_unix(arg1, arg2, arg3, arg4, arg5, arg6):
    return _pymod_libgop.gop_init_client_socket_unix(arg1, arg2, arg3, arg4, arg5, arg6)

def gop_close_connection(arg1):
    return _pymod_libgop.gop_close_connection(arg1)

def gop_close_init_connection(arg1):
    return _pymod_libgop.gop_close_init_connection(arg1)

def gop_close_active_connection(arg1):
    return _pymod_libgop.gop_close_active_connection(arg1)

def gop_read(arg1, myCharOutput, arg3):
    return _pymod_libgop.gop_read(arg1, myCharOutput, arg3)

def gop_write_command(arg1, arg2):
    return _pymod_libgop.gop_write_command(arg1, arg2)

def gop_get_cd(arg1):
    return _pymod_libgop.gop_get_cd(arg1)

cvar = _pymod_libgop.cvar
