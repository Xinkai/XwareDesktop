# -*- coding: utf-8 -*-

import logging
from launcher import app

from PyQt5.QtCore import QObject, pyqtSignal

import threading, time
import requests, json
from json.decoder import scanner, scanstring
from requests.exceptions import ConnectionError
from urllib.parse import unquote
from datetime import datetime


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
    sigTasksSummaryUpdated = pyqtSignal([bool], [dict])

    runningTasksStat = None
    completedTasksStat = None

    def __init__(self, parent):
        super().__init__(parent)

        # task stats
        self.runningTasksStat = RunningTaskStatistic(self)
        self.completedTasksStat = CompletedTaskStatistic(self)
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

            resCompleted = self._requestPollTasks(1)
            self.completedTasksStat.update(resCompleted)

            # emit summary, it doesn't matter using resRunning or resCompleted
            if resRunning is not None:
                self.sigTasksSummaryUpdated[dict].emit(resRunning)
            else:
                self.sigTasksSummaryUpdated[bool].emit(False)
            time.sleep(0.5)


class TaskStatistic(QObject):
    _tasks = None  # copy from _stat_mod upon it's done.
    _tasks_mod = None  # make changes to this one.

    TASK_STATES = {
        0: ("dload", "下载中"),
        8: ("wait", "等待中"),
        9: ("pause", "已停止"),
        10: ("pause", "已暂停"),
        11: ("finish", "已完成"),
        12: ("delete", "下载失败"),
        13: ("finish", "上传中"),
        14: ("wait", "提交中"),
        15: ("delete", "已删除"),
        16: ("delete", "已移至回收站"),
        37: ("wait", "已挂起"),
        38: ("delete", "发生错误"),
    }
    _initialized = False  # when the application starts up, it shouldn't fire.

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

    def getTasks(self):
        return self._tasks.copy()


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
        if self._initialized:
            # prevent already-completed tasks firing sigTaskCompleted
            #   when ETM starting later than frontend
            # by comparing `completeTime` with `timestamp`
            # threshold: 10 secs
            timestamp = datetime.timestamp(datetime.now())
            for completedId in completed:
                if 0 <= timestamp - self._tasks[completedId]["completeTime"] <= 10:
                    self.sigTaskCompleted.emit(completedId)
        else:
            self._initialized = True


class RunningTaskStatistic(TaskStatistic):
    sigTaskNolongerRunning = pyqtSignal(int)  # the task finished/recycled/wronged
    sigTaskAdded = pyqtSignal(int)
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
