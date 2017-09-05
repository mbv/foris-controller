#
# foris-controller
# Copyright (C) 2017 CZ.NIC, z.s.p.o. (http://www.nic.cz/)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA
#

import importlib
import inspect
import os
import pkgutil

from functools import wraps


class RWLock(object):
    """ Custom implementation of RWLock
        it can use lock for Processes as well as lock for threads
    """

    class ReadLock(object):
        def __init__(self, parent):
            self.parent = parent

        def __enter__(self):
            self.acquire()

        def __exit__(self, *args, **kwargs):
            self.release()

        def acquire(self):
            with self.parent._new_readers:
                with self.parent._counter_lock:
                    self.parent._counter += 1
                    self.parent._counter_lock.notify()

        def release(self):
            with self.parent._counter_lock:
                self.parent._counter -= 1
                self.parent._counter_lock.notify()

    class WriteLock(object):
        def __init__(self, parent):
            self.parent = parent

        def __enter__(self):
            self.acquire()

        def __exit__(self, *args, **kwargs):
            self.release()

        def acquire(self):
            self.parent._writer_lock.acquire()
            self.parent._new_readers.acquire()
            with self.parent._counter_lock:
                while self.parent._counter != 0:
                    self.parent._counter_lock.wait()

        def release(self):
            self.parent._new_readers.release()
            self.parent._writer_lock.release()

    def __init__(self, lock_module):
        """ Initializes RWLock

        :param lock_module: module which is used as locking backend - multiprocessing/threading
        """
        self._counter = 0
        self._writer_lock = lock_module.Lock()
        self._new_readers = lock_module.Lock()
        self._counter_lock = lock_module.Condition(lock_module.Lock())
        self.readlock = RWLock.ReadLock(self)
        self.writelock = RWLock.WriteLock(self)


def logger_wrapper(logger):
    """ Wraps funcion with some debug outputs of the logger

    :param logger: logger which will be used to trigger debug outputs
    :type logger: logging.Logger
    """
    def outer(func):
        @wraps(func)
        def inner(*args, **kwargs):
            logger.debug("Starting to perform '%s' (%s, %s)" % (func.__name__, args[1:], kwargs))
            res = func(*args, **kwargs)
            logger.debug("Performing '%s' finished (%s)." % (func.__name__, res))
            return res

        return inner

    return outer


def readlock(lock, logger):
    """ Make sure that this fuction is called after the read lock is obtained and
        wraps funcion with some debug outputs

    :param lock: lock which will be used
    :type lock: foris_controller.utils.RWLock
    :param logger: logger which will be used to trigger debug outputs
    :type logger: logging.Logger
    """
    def outer(func):
        @wraps(func)
        def inner(*args, **kwargs):
            logger.debug("Acquiring read lock for '%s'" % (func.__name__))
            with lock.readlock:
                return func(*args, **kwargs)
            logger.debug("Releasing read lock for '%s'" % (func.__name__))
        return inner
    return outer


def writelock(lock, logger):
    """ Make sure that this fuction is called after the write lock is obtained and
        wraps funcion with some debug outputs

    :param lock: lock which will be used
    :type lock: foris_controller.utils.RWLock
    :param logger: logger which will be used to trigger debug outputs
    :type logger: logging.Logger
    """
    def outer(func):
        @wraps(func)
        def inner(*args, **kwargs):
            logger.debug("Acquiring write lock for '%s'" % (func.__name__))
            with lock.writelock:
                return func(*args, **kwargs)
            logger.debug("Releasing write lock for '%s'" % (func.__name__))
        return inner
    return outer


def get_modules(filter_modules):
    """ Returns a list of modules that can be used

    :param filter_modules: use only modules which names are specified in this list
    :type filter_modules: list of str
    :returns: list of (module_name, module)
    """
    res = []
    modules = importlib.import_module("foris_controller_modules")
    for _, mod_name, _ in pkgutil.iter_modules(modules.__path__):
        if filter_modules and mod_name not in filter_modules:
            continue
        module = importlib.import_module("foris_controller_modules.%s" % mod_name)
        if hasattr(module, "Class"):
            res.append((mod_name, module))
    return res


def get_handler(module, base_handler_class):
    """ Instanciates a specific handler based on the module and base_handler class
    :param module: module which should be used
    :type module: module
    :param base_handler_class: base of the class which should be Openwrt/Mock/...
    :type base_handler_class: class
    :returns: handler instace or None
    """
    handlers_path = os.path.join(module.__path__[0], "handlers")
    for _, handler_name, _ in pkgutil.iter_modules([handlers_path]):
        # load <module>.handlers module
        handler_mod = importlib.import_module(
            ".".join([module.__name__, "handlers", handler_name]))

        # find subclass of base_handler (Mock/Openwrt)
        for _, handler_class in inspect.getmembers(handler_mod, inspect.isclass):
            if handler_class is not base_handler_class and \
                    issubclass(handler_class, base_handler_class):
                return handler_class()
