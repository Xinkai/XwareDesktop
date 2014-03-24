# -*- coding: utf-8 -*-

import logging

from PyQt5.QtCore import QObject, pyqtSignal
import threading, time
import requests, json
import collections
import pyinotify
from requests.exceptions import ConnectionError
from urllib.parse import unquote

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
    runningTasksStat = None
    completedTasksStat = None
    def __init__(self, app):
        super().__init__(app)
        self.app = app

        self.watchManager = pyinotify.WatchManager()
        self.notifier = pyinotify.ThreadedNotifier(self.watchManager,
                                                   self.dispatcher)
        self.notifier.name = "etmpy inotifier"
        self.notifier.daemon = True
        self.notifier.start()
        self.onEtmCfgChanged()
        self.watchManager.add_watch(constants.ETM_CFG_DIR, pyinotify.ALL_EVENTS)

        # task stats
        self.runningTasksStat = RunningTaskStatistic(self)
        self.completedTasksStat = CompletedTaskStatistic(self)
        self.t = threading.Thread(target = self.pollTasks, daemon = True,
                                  name = "tasks polling")
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

    def _requestPollTasks(self, kind): # kind means type, but type is a python reserved word.
        try:
            req = requests.get(self.lcontrol + "list?v=2&type={}&pos=0&number=99999&needUrl=1".format(kind))
            res = req.content.decode("utf-8")
            res = unquote(res)
            result = json.loads(res)
        except (ConnectionError, LocalCtrlNotAvailableError):
            result = None
        return result

    def pollTasks(self):
        while True:
            resRunning = self._requestPollTasks(0)
            self.runningTasksStat.update(resRunning)

            resCompleted = self._requestPollTasks(1)
            self.completedTasksStat.update(resCompleted)

            # emit summary, it doesn't matter using resRunning or resCompleted
            if resRunning:
                self.sigTasksSummaryUpdated[dict].emit(resRunning)
            else:
                self.sigTasksSummaryUpdated[bool].emit(False)
            time.sleep(0.5)

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

class TaskStatistic(QObject):
    _tasks = None # copy from _stat_mod upon it's done.
    _tasks_mod = None # make changes to this one.

    def __init__(self, parent):
        super().__init__(parent)
        self._tasks = {}
        self._tasks_mod = {}

    def getTIDs(self):
        tids = list(self._tasks.keys())
        return tids

    def getTask(self, tid):
        try:
            result = self._tasks[tid].copy()
        except KeyError:
            result = dict()
        return result

class CompletedTaskStatistic(TaskStatistic):
    sigTaskCompleted = pyqtSignal(int)

    def __init__(self, parent = None):
        super().__init__(parent)

    def update(self, data):
        if data is None:
            return

        # make a list of id of recent finished tasks
        completed = []

        self._tasks_mod.clear()
        for task in data["tasks"]:
            tid = task["id"]
            self._tasks_mod[tid] = task

            if tid not in self._tasks:
                completed.append(tid)

        self._tasks = self._tasks_mod.copy()
        for completedId in completed:
            self.sigTaskCompleted.emit(completedId)

class RunningTaskStatistic(TaskStatistic):
    SPEEDS_SAMPLES_COUNT = 25

    def __init__(self, parent = None):
        super().__init__(parent)

    def _getSpeeds(self, tid):
        try:
            result = self._tasks[tid]["speeds"]
        except KeyError:
            result = [0] * self.SPEEDS_SAMPLES_COUNT
        return result

    @staticmethod
    def _composeNewSpeeds(oldSpeeds, newSpeed):
        return oldSpeeds[1:] + [newSpeed]

    def update(self, data):
        if data is None:
            # if data is None, meaning request failed, push speed 0 to all tasks
            for tid, task in self._tasks.items():
                oldSpeeds = self._getSpeeds(tid)
                newSpeeds = self._composeNewSpeeds(oldSpeeds, 0)
                task["speeds"] = newSpeeds
            return

        self._tasks_mod.clear()
        for task in data["tasks"]:
            tid = task["id"]
            self._tasks_mod[tid] = task

            oldSpeeds = self._getSpeeds(tid)
            newSpeeds = self._composeNewSpeeds(oldSpeeds, task["speed"])
            self._tasks_mod[tid]["speeds"] = newSpeeds

        self._tasks = self._tasks_mod.copy()
