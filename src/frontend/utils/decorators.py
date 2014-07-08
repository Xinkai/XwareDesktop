# -*- coding: utf-8 -*-


def simplecache(func):
    """ useful to save values that doesn't change throughout the lifetime of this program. """
    cached = None
    ran = False

    def wrap(*args, **kwargs):
        nonlocal cached, ran
        if not ran:
            cached = func(*args, **kwargs)
            ran = True
        return cached
    return wrap
