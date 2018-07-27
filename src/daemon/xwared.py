#!/usr/bin/python3
# -*- coding: utf-8 -*-

import faulthandler, logging, os
from logging import handlers

import asyncio, json
import sys, time, fcntl, signal, threading
import collections
import subprocess
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../"))

import pyinotify

from shared import constants, XWARE_VERSION, DATE, XwaredSocketError
from shared.misc import debounce, tryRemove, tryClose
from shared.profile import profileBootstrap
from settings import SettingsAccessorBase, XWARED_DEFAULTS_SETTINGS


class XwaredServer(asyncio.Protocol):
    def __init__(self):
        self._transport = None
        self._data = b''

    def connection_made(self, transport):
        self._transport = transport

    def data_received(self, data):
        self._data += data

    def eof_received(self):
        try:
            bytesIn = self._data.decode("utf-8")
        except:
            return self._response({
                "error": XwaredSocketError.SERVER_DECODE,
            })

        try:
            payload = json.loads(bytesIn)
        except:
            return self._response({
                "error": XwaredSocketError.SERVER_JSON_LOAD,
            })

        try:
            method = getattr(xwared, "interface_" + payload.get("method"))
        except:
            return self._response({
                "error": XwaredSocketError.SERVER_NO_METHOD,
            })

        try:
            arguments = payload.get("arguments")
        except:
            return self._response({
                "error": XwaredSocketError.SERVER_NO_ARGUMENTS,
            })

        try:
            result = method(*arguments)
        except:
            return self._response({
                "error": XwaredSocketError.SERVER_EVALUATION,
            })

        self._response({
            "error": XwaredSocketError.SERVER_OK,
            "result": result,
        })

    def _response(self, response: dict):
        if "result" not in response:
            response["result"] = None

        response["error"] = int(response["error"])  # Compat for openSUSE 13.1 (Py3.3)
        responseBytes = json.dumps(response).encode("utf-8")
        self._transport.write(responseBytes)
        self._transport.close()


class ServerThread(threading.Thread):
    def __init__(self, _xwared):
        super().__init__(name = "Server", daemon = True)
        self._xwared = _xwared

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        asyncio.async(self._startEventLoop())
        loop.run_forever()

    @asyncio.coroutine
    def _startEventLoop(self):
        loop = asyncio.get_event_loop()
        yield from loop.create_unix_server(XwaredServer, constants.XWARED_SOCKET)


def setupLogging():
    loggingHandler = logging.handlers.RotatingFileHandler(
        os.path.expanduser("~/.xware-desktop/profile/xwared.log"),
        maxBytes = 1024 * 1024 * 5,
        backupCount = 5
    )
    logging.basicConfig(handlers = (loggingHandler,),
                        format = "%(asctime)s %(levelname)s:%(name)s:%(message)s")

    faultLogFd = open(os.path.expanduser('~/.xware-desktop/profile/xwared.fault.log'), 'a')
    faulthandler.enable(faultLogFd)


class Xwared(object):
    def __init__(self, log_novomit):
        super().__init__()
        self._log_novomit = log_novomit
        self.etmPid = 0
        self.fdLock = None
        self.toRunETM = None
        self.etmStartedAt = None
        self.etmLongevities = None

        # Cfg watchers
        self.etmCfg = dict()
        self.watchManager = None
        self.cfgWatcher = None

        # requirements checking
        self.ensureNonRoot()
        profileBootstrap(constants.PROFILE_DIR)
        setupLogging()

        self.ensureOneInstance()

        tryRemove(constants.XWARED_SOCKET)

        # initialize variables
        signal.signal(signal.SIGTERM, self.unload)
        signal.signal(signal.SIGINT, self.unload)
        self.settings = SettingsAccessorBase(constants.XWARED_CONFIG_FILE,
                                             XWARED_DEFAULTS_SETTINGS)
        self.toRunETM = self.settings.getbool("xwared", "startetm")
        self.etmLogs = collections.deque(maxlen = 250)
        self._resetEtmLongevities()

        # ipc listener
        self.listener = ServerThread(self)
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

    @staticmethod
    def ensureNonRoot():
        if os.getuid() == 0 or os.geteuid() == 0:
            print("拒绝以root运行", file = sys.stderr)
            sys.exit(-1)

    def ensureOneInstance(self):
        # If one instance is already running, shout so and then exit the program
        # otherwise, a) hold the lock to xwared, b) prepare etm lock
        self.fdLock = os.open(constants.XWARED_LOCK, os.O_CREAT | os.O_RDWR)
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

        env = os.environ.copy()
        env.update(CHMNS_LD_PRELOAD = constants.ETM_PATCH_FILE)

        if self._log_novomit:
            additionals = dict(
                stdout = subprocess.PIPE,
                stderr = subprocess.STDOUT,
            )
        else:
            additionals = dict()
        if __debug__:
            proc = subprocess.Popen(('/opt/xware-desktop/chmns', '/opt/xware-desktop/xware/lib/EmbedThunderManager', '--verbose'),
                                    env=env,
                                    **additionals)
        else:
            proc = subprocess.Popen(constants.ETM_COMMANDLINE,
                                env=env,
                                **additionals)
        self.etmPid = proc.pid
        if self.etmPid:
            self.etmStartedAt = time.monotonic()
            self._watchETM(proc)
        else:
            print("Cannot start etm", file = sys.stderr)
            sys.exit(1)

    def _resetEtmLongevities(self):
        sampleNumber = self.settings.getint("etm", "samplenumberoflongevity")
        if not isinstance(self.etmLongevities, collections.deque):
            self.etmLongevities = collections.deque(maxlen = sampleNumber)

        for i in range(sampleNumber):
            self.etmLongevities.append(float("inf"))

    def _watchETM(self, proc):
        if self._log_novomit:
            for line in iter(proc.stdout.readline, b""):
                line = line.rstrip().decode("utf-8")
                self.etmLogs.append(line)

        ret = proc.wait()
        self.etmPid = 0
        if self._log_novomit:
            if ret != 0:
                print("\n".join(self.etmLogs), file=sys.stderr)
            self.etmLogs.clear()

        longevity = time.monotonic() - self.etmStartedAt
        self.etmLongevities.append(longevity)
        threshold = self.settings.getint("etm", "shortlivedthreshold")
        if all(map(lambda l: l <= threshold, self.etmLongevities)):
            print("xwared: ETM持续时间连续{number}次不超过{threshold}秒，终止执行ETM"
                  .format(number=self.etmLongevities.maxlen,
                          threshold=threshold),
                  file=sys.stderr)
            print("这极有可能是xware本身的bug引起的，更多信息请看 "
                  "https://github.com/Xinkai/XwareDesktop/wiki/故障排查和意见反馈"
                  "#etm持续时间连续3次不超过30秒终止执行etm的调试方法", file = sys.stderr)
            self.toRunETM = False

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
    @staticmethod
    def interface_versions():
        return {
            "xware": XWARE_VERSION,
            "api": DATE,
        }

    def interface_startETM(self):
        self._resetEtmLongevities()
        self.toRunETM = True

    def interface_stopETM(self):
        self._resetEtmLongevities()
        self.stopETM(False)

    def interface_restartETM(self):
        self._resetEtmLongevities()
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

    def interface_setStartEtmWhen(self, startetmwhen):
        self.settings.setint("xwared", "startetmwhen", startetmwhen)
        if startetmwhen == 1:
            self.settings.setbool("xwared", "startetm", True)
        self.settings.save()

    def interface_setMounts(self, mounts):
        raise NotImplementedError()

    def interface_getMounts(self):
        raise NotImplementedError()

    def interface_infoPoll(self):
        return {
            "etmPid": self.etmPid,
            "lcPort": int(self.etmCfg.get("local_control.listen_port", 0)),
            "peerId": self.etmCfg.get("rc.peerid", ""),
            "startEtmWhen": int(self.settings.getint("xwared", "startetmwhen")),
        }

    def unload(self, sig, stackframe):
        print("unloading...")
        self.stopETM(False)

        tryClose(self.fdLock)
        tryRemove(constants.XWARED_LOCK)
        self.settings.save()

        sys.exit(0)

if __name__ == "__main__":
    novomit = "--log-novomit" in sys.argv
    xwared = Xwared(novomit)
    while True:
        xwared.runETM()
