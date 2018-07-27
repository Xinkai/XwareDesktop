# -*- coding: utf-8 -*-

import logging
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices

import enum
from collections import defaultdict, namedtuple
from itertools import groupby
import os, subprocess, sys

from .decorators import simplecache


@enum.unique
class InitType(enum.Enum):
    SYSTEMD = 1
    UPSTART = 2
    UPSTART_WITHOUT_USER_SESSION = 3
    WINDOWS = 4
    UNKNOWN = 5


@simplecache
def getInitType():
    if sys.platform == "linux":
        # try read /proc/1/stat
        with open("/proc/1/stat") as f:
            pid1Name = f.read().split(" ")[1]  # 2nd item
            if pid1Name == "(systemd)":
                return InitType.SYSTEMD

        # try read keyword in "init --version"
        try:
            with subprocess.Popen(["init", "--version"], stdout = subprocess.PIPE) as proc:
                initVersion = str(proc.stdout.read())
        except FileNotFoundError:
            initVersion = None
        except PermissionError:
            # workaround #151: weird permission error on Mint 17
            print("#151: weird permission error", file = sys.stderr)
            initVersion = None

        if initVersion:
            if "systemd" in initVersion:
                return InitType.SYSTEMD
            elif "upstart" in initVersion:
                if "UPSTART_SESSION" in os.environ:
                    return InitType.UPSTART
                else:
                    return InitType.UPSTART_WITHOUT_USER_SESSION

        # try resolve symlink
        for path in ("/usr/sbin/init", "/sbin/init"):
            try:
                realInitPath = os.readlink(path)
            except FileNotFoundError:
                realInitPath = ""
            except OSError as osErr:
                import errno
                if osErr.errno == errno.EINVAL:
                    # Not a symlink
                    realInitPath = ""
                else:
                    raise

            if realInitPath.endswith("systemd"):
                return InitType.SYSTEMD

        # tried everything
        return InitType.UNKNOWN

    elif sys.platform == "win32":
        return InitType.WINDOWS

    return InitType.UNKNOWN


@enum.unique
class FileManagerType(enum.Enum):
    Dolphin = 1
    Thunar = 2
    PCManFM = 3
    Nemo = 4
    Nautilus = 5
    Explorer = 6
    Unknown = 7


@simplecache
def getFileManagerType():
    if sys.platform == "linux":
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
    elif sys.platform == "win32":
        return FileManagerType.Explorer

    return FileManagerType.Unknown


def runAsIndependentProcess(line: "ls -al" or "['ls', '-al']"):
    """
    Useful when we don't care about input/output/return value.
    :param line: command line to run
    :return: None
    """
    p = subprocess.Popen(line, stdin = None, stdout = None, stderr = None)
    logging.info("Started {} with pid {}".format(line, p.pid))


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
            runAsIndependentProcess(["dolphin", "--select"] + d[path])
    else:
        # Thunar, PCManFM, Nemo don't support select at all!
        # Nautilus doesn't support selecting multiple files.
        # fallback using systemOpen
        for path in d:
            systemOpen(path)


def viewOneFile(file: "str of file path"):
    fileManager = getFileManagerType()
    if fileManager == FileManagerType.Dolphin:
        runAsIndependentProcess(["dolphin", "--select"] + [file])
    elif fileManager == FileManagerType.Nautilus:
        runAsIndependentProcess(["nautilus", "--select"] + [file])
    elif fileManager == FileManagerType.Explorer:
        runAsIndependentProcess(["explorer", "/select,{}".format(file)])
    else:
        # fallback
        systemOpen(os.path.dirname(file))


@simplecache
def getCurrentSessionId():
    if sys.platform == "win32":
        import ctypes
        from ctypes.wintypes import DWORD
        pid = os.getpid()
        result = DWORD()
        ok = ctypes.windll.kernel32.ProcessIdToSessionId(pid, ctypes.byref(result))
        if not ok:
            error = ctypes.GetLastError()
            raise WindowsError(error)
        return result.value
    else:
        raise NotImplementedError()

Distro = namedtuple("Distro", ["id", "name", "version"])


@simplecache
def getDistro():
    # Returns a (id, pretty_name, version_id) tuple
    assert sys.platform == "linux"

    try:
        with open("/etc/os-release", encoding = "UTF-8") as f:
            lines = f.read()

        import shlex
        parsed = shlex.split(lines)  # a list of "KEY=VALUE"
        parsedDict = dict(map(lambda s: s.split("=", maxsplit = 1), parsed))
        return Distro(id = parsedDict.get("ID", "Unknown"),
                      name = parsedDict.get("PRETTY_NAME", parsedDict.get("NAME", "Unknown")),
                      version = parsedDict.get("VERSION_ID", parsedDict.get("VERSION", "")))
    except FileNotFoundError:
        return Distro(id = "Unknown",
                      name = "Unknown",
                      version = "")
