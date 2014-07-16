# -*- coding: utf-8 -*-

import enum
import os, subprocess

from .decorators import simplecache


@enum.unique
class InitType(enum.Enum):
    SYSTEMD = 1
    UPSTART = 2
    UPSTART_WITHOUT_USER_SESSION = 3
    UNKNOWN = 4


@simplecache
def getInitType():
    with subprocess.Popen(["init", "--version"], stdout = subprocess.PIPE) as proc:
        initVersion = str(proc.stdout.read())

    if "systemd" in initVersion:
        return InitType.SYSTEMD
    elif "upstart" in initVersion:
        if "UPSTART_SESSION" in os.environ:
            return InitType.UPSTART
        else:
            return InitType.UPSTART_WITHOUT_USER_SESSION
    else:
        return InitType.UNKNOWN
