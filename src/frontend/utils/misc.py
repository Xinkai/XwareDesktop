# -*- coding: utf-8 -*-

import base64

from shared.misc import *
from enum import IntEnum


def getHumanBytesNumber(byteNum):
    kilo = 1024
    mega = kilo * kilo

    if byteNum >= mega:
        return "{:.2f}MiB".format(byteNum / mega)
    else:
        return "{:.2f}KiB".format(byteNum / kilo)


def decodePrivateLink(link):
    # try to return the real link behind thunder:// flashget:// qqdl://
    if "\n" in link or "\t" in link or "\r" in link:
        raise Exception("decodePrivateLink Failed. "
                        "Maybe passed in multiple private links? {}".format(link))

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


def dropPy34Enum(pyenum: IntEnum):
    # convert a python 3.4 IntEnum class to a plain class that can be used with Q_ENUMS
    assert issubclass(pyenum, IntEnum)
    name = pyenum.__class__.__name__
    d = {}
    for member in pyenum.__members__:
        d[member] = int(getattr(pyenum, member))

    klass = type(name, (object,), d)
    return klass
