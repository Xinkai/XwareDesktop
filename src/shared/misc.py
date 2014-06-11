# -*- coding: utf-8 -*-

from threading import Timer
import os

try:
    from pathlib import Path
except ImportError:
    from shared.backports.pathlib import Path


def debounce(wait, instant_first = True):
    # skip all calls that are invoked for a certain period of time, except for the last one.

    def debouncer(func):
        def debounced(*args, **kwargs):
            def call():
                return func(*args, **kwargs)

            if instant_first:
                if not hasattr(debounced, "initial_ran"):
                    setattr(debounced, "initial_ran", True)
                    return call()

            if hasattr(debounced, "t"):
                debounced.t.cancel()

            debounced.t = Timer(wait, call)
            debounced.t.daemon = True
            debounced.t.name = "debounced {}".format(func.__name__)
            debounced.t.start()
        return debounced
    return debouncer


def trySymlink(src, dest):
    # ignores the exception when dest is already there.
    try:
        os.symlink(src, dest)
    except FileExistsError:
        pass


def tryRemove(path):
    # ignores the exception when path doesn't exist.
    try:
        os.remove(path)
    except FileNotFoundError:
        pass


def tryClose(fd):
    # ignores OSError, useful when exiting the program and we no longer care.
    try:
        os.close(fd)
    except OSError:
        pass


def tryMkdir(pathstr):
    # mimics "mkdir -p"
    try:
        Path(pathstr).mkdir(parents = True)
    except FileExistsError:
        pass
