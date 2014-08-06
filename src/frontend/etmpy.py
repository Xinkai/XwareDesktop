# -*- coding: utf-8 -*-

import logging
from launcher import app

from PyQt5.QtCore import QObject, pyqtSignal

import threading, time
import requests, json
from json.decoder import scanner, scanstring
from requests.exceptions import ConnectionError
from urllib.parse import unquote


class LocalCtrlNotAvailableError(BaseException):
    pass


class _TaskPollingJsonDecoder(json.JSONDecoder):
    # This class automatically unquotes URL-quoted characters like %20
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.parse_string = self.unquote_parse_string
        # "rebuild" scan_once
        # scanner.c_make_scanner doesn't seem to support custom parse_string.
        self.scan_once = scanner.py_make_scanner(self)

    @staticmethod
    def unquote_parse_string(*args, **kwargs):
        result = scanstring(*args, **kwargs)  # => (str, end_index)
        unquotedResult = (unquote(result[0]), result[1])
        return unquotedResult


class EtmPy(QObject):
    def __init__(self, parent):
        super().__init__(parent)

        # task stats
        self.runningTasksStat = RunningTaskStatistic(self)
        self.t = threading.Thread(target = self.pollTasks, daemon = True,
                                  name = "tasks polling")
        self.t.start()

    @property
    def lcontrol(self):
        lcPort = app.adapterManager[0].lcPort
        if not lcPort:
            raise LocalCtrlNotAvailableError()
        return "http://127.0.0.1:{}/".format(lcPort)

    def _requestPollTasks(self, kind):  # kind means type, but type is a python reserved word.
        try:
            req = requests.get(self.lcontrol +
                               "list?v=2&type={}&pos=0&number=99999&needUrl=1".format(kind))
            res = req.content.decode("utf-8")
            result = json.loads(res, cls = _TaskPollingJsonDecoder)
        except (ConnectionError, LocalCtrlNotAvailableError):
            result = None
        return result

    def pollTasks(self):
        while True:
            resRunning = self._requestPollTasks(0)
            self.runningTasksStat.update(resRunning)
            time.sleep(0.5)


class TaskStatistic(QObject):
    def __init__(self, parent):
        super().__init__(parent)
        self._tasks = {}  # copy from _stat_mod upon it's done.
        self._tasks_mod = {}  # make changes to this one.
        self._initialized = False  # when the application starts up, it shouldn't fire.

    def getTIDs(self):
        tids = list(self._tasks.keys())
        return tids

    def getTasks(self):
        return self._tasks.copy()


class RunningTaskStatistic(TaskStatistic):
    sigTaskNolongerRunning = pyqtSignal(int)  # the task finished/recycled/wronged
    sigTaskAdded = pyqtSignal(int)

    def __init__(self, parent = None):
        super().__init__(parent)

    def update(self, data):
        if data is None:
            return

        self._tasks_mod.clear()
        for task in data["tasks"]:
            tid = task["id"]
            self._tasks_mod[tid] = task

        prevTaskIds = set(self.getTIDs())
        currTaskIds = set(self._tasks_mod.keys())

        nolongerRunning = prevTaskIds - currTaskIds
        added = currTaskIds - prevTaskIds

        self._tasks = self._tasks_mod.copy()
        if self._initialized:
            for nolongerRunningId in nolongerRunning:
                self.sigTaskNolongerRunning.emit(nolongerRunningId)
            for addedId in added:
                self.sigTaskAdded.emit(addedId)
        else:
            self._initialized = True
