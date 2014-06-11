# -*- coding: utf-8 -*-

import base64
import subprocess

from shared.misc import *


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

INIT_SYSTEMD = 1
INIT_UPSTART = 2
INIT_UPSTART_WITHOUT_USER_SESSION = 3
INIT_UNKNOWN = 4


def getInitSystemType():
    with subprocess.Popen(["init", "--version"], stdout = subprocess.PIPE) as proc:
        initVersion = str(proc.stdout.read())

    if "systemd" in initVersion:
        return INIT_SYSTEMD
    elif "upstart" in initVersion:
        if "UPSTART_SESSION" in os.environ:
            return INIT_UPSTART
        else:
            return INIT_UPSTART_WITHOUT_USER_SESSION
    else:
        return INIT_UNKNOWN
