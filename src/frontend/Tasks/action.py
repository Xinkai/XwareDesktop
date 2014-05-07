# -*- coding: utf-8 -*-

import logging
from launcher import app

from PyQt5.QtCore import QObject, pyqtSlot

import sys
from urllib import parse

from frontendpy import FrontendAction
import misc
from .mimeparser import UrlExtractor
from .watchers.clipboard import ClipboardWatcher
from .watchers.commandline import CommandlineWatcher


class CreateTasksAction(FrontendAction):
    _tasks = None  # tasks to add in the same batch

    def __init__(self, tasks):
        super().__init__()
        self._tasks = tasks

    def __repr__(self):
        return "{} {}".format(self.__class__.__name__, self._tasks)

    def consume(self):
        taskUrls = list(map(lambda task: task.url, self._tasks))
        if self._tasks[0].kind == CreateTask.NORMAL:
            app.frontendpy.sigCreateTasks.emit(taskUrls)
        else:
            app.mainWin.page.overrideFile = taskUrls[0]
            app.frontendpy.sigCreateTaskFromTorrentFile.emit()


class CreateTask(object):
    NORMAL = 0
    LOCAL_TORRENT = 1

    url = None
    kind = None

    def __init__(self, url = None, kind = None):
        self.url = url

        if kind is None:
            kind = self.NORMAL
        self.kind = kind

    def __repr__(self):
        return "{} <{}>".format(self.__class__.__name__, self.url)


class TaskCreationAgent(QObject):
    _urlExtractor = None

    def __init__(self, parent = None):
        super().__init__(parent)
        # hold a reference to the parent, aka frontendpy.
        # when the program is launched, app.frontendpy would be None.
        self._frontendpy = parent
        tasks = sys.argv[1:]
        if tasks:
            self.createTasksAction(tasks)

        self._urlExtractor = UrlExtractor(self)
        app.sigMainWinLoaded.connect(self.connectUI)

        # load watchers
        self._clipboardWatcher = ClipboardWatcher(self)
        self._commandlineWatcher = CommandlineWatcher(self)

    @pyqtSlot()
    def connectUI(self):
        app.mainWin.action_createTask.triggered.connect(self.createTasksAction)

    def createTasksFromMimeData(self, data):
        # This method only checks text data.
        urls = self._urlExtractor.extract(data.text())
        if len(urls) > 0:
            self.createTasksAction(urls)

    @pyqtSlot()
    @pyqtSlot(list)
    def createTasksAction(self, taskUrls = None):
        if taskUrls:
            alltasks = self._filterInvalidTasks(map(self._createTask, taskUrls))
            tasks = list(filter(lambda task: task.kind == CreateTask.NORMAL, alltasks))
            tasks_localtorrent = list(filter(lambda task: task.kind == CreateTask.LOCAL_TORRENT,
                                             alltasks))
        else:
            # else
            tasks = self._filterInvalidTasks([self._createTask()])
            tasks_localtorrent = []

        if tasks:
            self._frontendpy.queueAction(CreateTasksAction(tasks))
        for task_bt in tasks_localtorrent:  # because only 1 bt-task can be added once.
            self._frontendpy.queueAction(CreateTasksAction([task_bt]))

    @staticmethod
    def _filterInvalidTasks(tasks):
        # remove those urls which were not recognized by self._createTask
        return list(filter(lambda t: t is not None, tasks))

    @staticmethod
    def _createTask(taskUrl = None):
        if taskUrl is None:
            return CreateTask()

        if taskUrl.startswith("file://"):
            taskUrl = taskUrl[len("file://"):]

        parsed = parse.urlparse(taskUrl)
        if parsed.scheme in ("thunder", "flashget", "qqdl"):
            url = misc.decodePrivateLink(taskUrl)
            return CreateTask(url)

        elif parsed.scheme == "":
            if parsed.path.endswith(".torrent"):
                return CreateTask(taskUrl, kind = CreateTask.LOCAL_TORRENT)

        elif parsed.scheme in ("http", "https", "ftp", "magnet", "ed2k"):
            return CreateTask(taskUrl)
