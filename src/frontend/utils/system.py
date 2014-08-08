# -*- coding: utf-8 -*-

from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices

import enum
from collections import defaultdict
from itertools import groupby
import os, subprocess, errno

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
        # On Fedora "init --version" gives an error
        # Use an alternative method
        try:
            realInitPath = os.readlink("/usr/sbin/init")
            if realInitPath.endswith("systemd"):
                return InitType.SYSTEMD
        except FileNotFoundError:
            pass
        except OSError as e:
            if e.errno == errno.EINVAL:
                pass  # Not a symlink
            else:
                raise e  # rethrow

        return InitType.UNKNOWN


@enum.unique
class FileManagerType(enum.Enum):
    Dolphin = 1
    Thunar = 2
    PCManFM = 3
    Nemo = 4
    Nautilus = 5
    Unknown = 6


@simplecache
def getFileManagerType():
    with subprocess.Popen(["xdg-mime", "query", "default", "inode/directory"],
                          stdout = subprocess.PIPE) as proc:
        output = str(proc.stdout.read()).lower()

    if "dolphin" in output:
        return FileManagerType.Dolphin
    elif "nautilus" in output:
        return FileManagerType.Nautilus
    elif "nemo" in output:
        return FileManagerType.Nemo
    elif "pcmanfm" in output:
        return FileManagerType.PCManFM
    elif "thunar" in output:
        return FileManagerType.Thunar

    return FileManagerType.Unknown


def runAsIndependentProcess(line: "ls -al" or "['ls', '-al']"):
    """
    Useful when we don't care about input/output/return value.
    :param line: command line to run
    :return: None
    """
    if type(line) is str:
        cmd = line.split(" ")
    else:
        cmd = line

    pid = os.fork()
    if pid == 0:
        # child
        os.execvp(cmd[0], cmd)
    else:
        return


def systemOpen(url: str):
    qUrl = QUrl.fromLocalFile(url)
    QDesktopServices.openUrl(qUrl)


def viewMultipleFiles(files: "list<str of file paths>"):
    files = sorted(files)

    d = defaultdict(list)
    for path, filenames in groupby(files, key = os.path.dirname):
        for filename in filenames:
            d[path].append(filename)

    fileManager = getFileManagerType()

    if fileManager == FileManagerType.Dolphin:
        for path in d:
            # TODO: escape filenames
            runAsIndependentProcess("dolphin --select {}".format(" ".join(d[path])))
    else:
        # Thunar, PCManFM, Nemo don't support select at all!
        # Nautilus doesn't support selecting multiple files.
        # fallback using systemOpen
        for path in d:
            systemOpen(path)


def viewOneFile(file: "str of file path"):
    fileManager = getFileManagerType()
    # TODO: escape filename
    if fileManager == FileManagerType.Dolphin:
        runAsIndependentProcess("dolphin --select {}".format(file))
    elif fileManager == FileManagerType.Nautilus:
        runAsIndependentProcess("nautilus --select {}".format(file))
    else:
        # fallback
        systemOpen(os.path.dirname(file))
