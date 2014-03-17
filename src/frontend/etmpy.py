# -*- coding: utf-8 -*-

from PyQt5.QtCore import QObject, pyqtSignal
import threading, time
import requests
import collections
import pyinotify
from requests.exceptions import ConnectionError

import constants
from misc import debounce
log = print

class LocalCtrlNotAvailableError(BaseException):
    pass

EtmSetting = collections.namedtuple("EtmSetting", ["dLimit", "uLimit", "maxRunningTasksNum"])
ActivationStatus = collections.namedtuple("ActivationStatus", ["userid", "status", "code", "peerid"])

class EtmPy(QObject):
    sigTasksSummaryUpdated = pyqtSignal([bool], [dict])
    sigCfgChanged = pyqtSignal()

    cfg = {}

    def __init__(self, app):
        super().__init__(app)
        self.app = app

        self.watchManager = pyinotify.WatchManager()
        self.notifier = pyinotify.ThreadedNotifier(self.watchManager,
                                                   self.dispatcher)
        self.notifier.name = "etmpy inotifier"
        self.notifier.daemon = True
        self.notifier.start()
        self.app.lastWindowClosed.connect(lambda: self.notifier.stop())
        self.onEtmCfgChanged()
        self.watchManager.add_watch(constants.ETM_CFG_DIR, pyinotify.ALL_EVENTS)

        self.t = threading.Thread(target = self.getCurrentTasksSummary, daemon = True,
                                  name = "tasks summary polling")
        self.t.start()

    @debounce(0.5, instant_first=True)
    def onEtmCfgChanged(self):
        with open(constants.ETM_CFG_FILE, 'r') as file:
            lines = file.readlines()

        pairs = {}
        for line in lines:
            eq = line.index("=")
            k = line[:eq]
            v = line[(eq+1):].strip()
            pairs[k] = v
        self.cfg = pairs

    def dispatcher(self, event):
        if event.maskname != "IN_CLOSE_WRITE":
            return

        if event.pathname == constants.ETM_CFG_FILE:
            self.onEtmCfgChanged()

    @property
    def lcontrol(self):
        lcport = self.cfg.get("local_control.listen_port", None)

        try:
            lcport = int(lcport)
        except (ValueError, TypeError):
            raise LocalCtrlNotAvailableError

        return "http://127.0.0.1:{}/".format(lcport)

    def getSettings(self):
        try:
            req = requests.get(self.lcontrol + "getspeedlimit")
            limits = req.json()[1:] # not sure about what first element means, ignore for now

            req = requests.get(self.lcontrol + "getrunningtaskslimit")
            maxRunningTasksNum = req.json()[1]

            return EtmSetting(dLimit = limits[0], uLimit = limits[1],
                              maxRunningTasksNum = maxRunningTasksNum)
        except (ConnectionError, LocalCtrlNotAvailableError):
            return False

    def saveSettings(self, newsettings):
        requests.post(self.lcontrol + \
                      "settings?downloadSpeedLimit={}&uploadSpeedLimit={}&maxRunTaskNumber={}".format(*newsettings))

    def getCurrentTasksSummary(self):
        while True:
            try:
                req = requests.get(self.lcontrol + "list?v=2&type=1&pos=0&number=0&needUrl=1")
                res = req.json()
                self.sigTasksSummaryUpdated[dict].emit(res)
            except (ConnectionError, LocalCtrlNotAvailableError):
                self.sigTasksSummaryUpdated[bool].emit(False)
            time.sleep(2)

    def getActivationStatus(self):
        try:
            req = requests.get(self.lcontrol + "getsysinfo")
            res = req.json()
            status = res[3] # 1 - bound, 0 - unbound
            code = res[4]
        except (ConnectionError, LocalCtrlNotAvailableError):
            status = -1 # error
            code = None

        userid = self.cfg.get("userid", 0)
        try:
            userid = int(userid)
        except ValueError:
            userid = 0 # unbound -> 0

        peerid = self.cfg.get("rc.peerid", "")

        result = ActivationStatus(userid, status, code, peerid)
        return result
