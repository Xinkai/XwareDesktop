# -*- coding: utf-8 -*-

from threading import Timer
import base64

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
            debounced.t.daemon = True
            debounced.t.name = "debounced {}".format(func.__name__)
            debounced.t.start()
        return debounced
    return debouncer

def decodePrivateLink(link):
    # try to return the real link behind thunder:// flashget:// qqdl://
    if "\n" in link and \
        "\t" in link and \
        "\r" in link:
        raise Exception("decodePrivateLink Failed. Maybe passed in multiple private links? {}".format(link))

    scheme, *path = link.split("://")
    assert len(path) == 1, "Invalid private link {}.".format(link)

    path = path[0].encode("utf-8")
    decoded = base64.urlsafe_b64decode(path).decode("utf-8")

    scheme = scheme.lower()
    if scheme == "thunder":
        if decoded.startswith("AA") and decoded.endswith("ZZ"):
            return decoded[2:-2]
    elif scheme == "flashget":
        if decoded.startswith("[FLASHGET]") and decoded.endswith("[FLASHGET]"):
            return decoded[10:-10]
    elif scheme == "qqdl":
        return decoded
    else:
        raise Exception("Cannot decode private link {}.".format(link))
