#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging

import sys, os, time, fcntl, signal, threading
from multiprocessing.connection import Listener
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../"))

import pyinotify

from shared import constants, BackendInfo
from shared.misc import debounce
from settings import SettingsAccessorBase, XWARED_DEFAULTS_SETTINGS


class XwaredCommunicationListener(threading.Thread):
    def __init__(self, _xwared):
        super().__init__(daemon = True,
                         name = "xwared communication listener")
        self._xwared = _xwared

    def run(self):
        with Listener(*constants.XWARED_SOCKET) as listener:
            while True:
                with listener.accept() as conn:
                    func, args, kwargs = conn.recv()
                    response = getattr(self._xwared, "interface_" + func)(*args, **kwargs)
                    conn.send(response)


class Xwared(object):
    etmPid = 0
    fdLock = None
    toRunETM = None

    # Cfg watchers
    etmCfg = dict()
    watchManager = None
    cfgWatcher = None

    def __init__(self):
        super().__init__()
        # requirements checking
        self.ensureOneInstance()

        # initialize variables
        signal.signal(signal.SIGTERM, self.unload)
        signal.signal(signal.SIGINT, self.unload)
        self.settings = SettingsAccessorBase(constants.XWARED_CONFIG_FILE,
                                             XWARED_DEFAULTS_SETTINGS)
        self.toRunETM = self.settings.getbool("xwared", "startetm")

        # ipc listener
        self.listener = XwaredCommunicationListener(self)
        self.listener.start()

        # using pyinotify to monitor etm.cfg changes
        self.setupCfgWatcher()

    def setupCfgWatcher(self):
        # etm.cfg watcher
        self.watchManager = pyinotify.WatchManager()
        self.cfgWatcher = pyinotify.ThreadedNotifier(self.watchManager,
                                                     self.pyinotifyDispatcher)
        self.cfgWatcher.name = "cfgWatcher inotifier"
        self.cfgWatcher.daemon = True
        self.cfgWatcher.start()
        self.watchManager.add_watch(constants.ETM_CFG_DIR, pyinotify.ALL_EVENTS)

    @debounce(0.5, instant_first=True)
    def onEtmCfgChanged(self):
        try:
            with open(constants.ETM_CFG_FILE, 'r') as file:
                lines = file.readlines()

            pairs = {}
            for line in lines:
                eq = line.index("=")
                k = line[:eq]
                v = line[(eq + 1):].strip()
                pairs[k] = v
            self.etmCfg = pairs
        except FileNotFoundError:
            print("Xware Desktop: etm.cfg not present at the moment.")

    def pyinotifyDispatcher(self, event):
        if event.maskname != "IN_CLOSE_WRITE":
            return

        if event.pathname == constants.ETM_CFG_FILE:
            self.onEtmCfgChanged()

    def ensureOneInstance(self):
        # If one instance is already running, shout so and then exit the program
        # otherwise, a) hold the lock to xwared, b) prepare etm lock
        self.fdLock = os.open(constants.XWARED_LOCK, os.O_CREAT | os.O_RDWR, 0o666)
        try:
            fcntl.flock(self.fdLock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("xwared已经运行", file = sys.stderr)
            sys.exit(-1)

        print("xwared: unlocked")

    def runETM(self):
        while not self.toRunETM:
            time.sleep(1)

        if self.settings.getint("xwared", "startetmwhen") == 2:
            self.settings.setbool("xwared", "startetm", True)
            self.settings.save()

        self.toRunETM = True
        try:
            self.etmPid = os.fork()
        except OSError:
            print("Fork failed", file = sys.stderr)
            sys.exit(-1)

        if self.etmPid == 0:
            # child
            os.putenv("CHMNS_LD_PRELOAD", constants.ETM_PATCH_FILE)
            print("child: pid({pid}) ppid({ppid})".format(pid = os.getpid(),
                                                          ppid = self.etmPid))
            cmd = constants.ETM_COMMANDLINE
            os.execv(cmd[0], cmd)
            sys.exit(-1)
        else:
            # parent
            print("parent: pid({pid}) cpid({cpid})".format(pid = os.getpid(),
                                                           cpid = self.etmPid))
            self._watchETM()

    def _watchETM(self):
        os.waitpid(self.etmPid, 0)
        self.etmPid = 0

    def stopETM(self, restart):
        if self.etmPid:
            self.toRunETM = restart
            os.kill(self.etmPid, signal.SIGTERM)
        else:
            print("ETM not running, ignore stopETM")
        if self.settings.getint("xwared", "startetmwhen") == 2:
            self.settings.setbool("xwared", "startetm", restart)
            self.settings.save()

    # frontend end interfaces
    def interface_startETM(self):
        self.toRunETM = True

    def interface_stopETM(self):
        self.stopETM(False)

    def interface_restartETM(self):
        self.stopETM(True)

    def interface_start(self):
        if self.settings.getint("xwared", "startetmwhen") == 3:
            self.interface_startETM()
            self.settings.setbool("xwared", "startetm", True)
            self.settings.save()

    def interface_quit(self):
        if self.settings.getint("xwared", "startetmwhen") == 3:
            self.stopETM(False)
            self.settings.setbool("xwared", "startetm", True)
            self.settings.save()

    def interface_getStartEtmWhen(self):
        return self.settings.getint("xwared", "startetmwhen")

    def interface_setStartEtmWhen(self, startetmwhen):
        self.settings.setint("xwared", "startetmwhen", startetmwhen)
        if startetmwhen == 1:
            self.settings.setbool("xwared", "startetm", True)
        self.settings.save()

    def interface_setMounts(self, mounts):
        raise NotImplementedError()

    def interface_getMounts(self):
        raise NotImplementedError()

    def interface_permissionCheck(self):
        raise NotImplementedError()

    def interface_infoPoll(self):
        return BackendInfo(etmPid = self.etmPid,
                           lcPort = int(self.etmCfg.get("local_control.listen_port", 0)),
                           userId = int(self.etmCfg.get("userid", 0)),
                           peerId = self.etmCfg.get("rc.peerid", ""))

    @staticmethod
    def tryClose(fd):
        try:
            os.close(fd)
        except OSError:
            pass

    @staticmethod
    def tryRemove(path):
        try:
            os.remove(path)
        except OSError:
            pass

    def unload(self, sig, stackframe):
        print("unloading...")
        self.stopETM(False)

        self.tryClose(self.fdLock)
        self.tryRemove(constants.XWARED_LOCK)
        self.settings.save()

        sys.exit(0)

if __name__ == "__main__":
    from shared.profile import profileBootstrap
    profileBootstrap(constants.PROFILE_DIR)
    xwared = Xwared()
    while True:
        xwared.runETM()
