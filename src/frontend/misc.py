# -*- coding: utf-8 -*-

from threading import Timer

def getHumanBytesNumber(byteNum):
    kilo = 1024
    mega = kilo * kilo

    if byteNum >= mega:
        return "{:.2f}MB".format(byteNum / mega)
    else:
        return "{:.2f}KB".format(byteNum / kilo)

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
            debounced.t.start()
        return debounced
    return debouncer
