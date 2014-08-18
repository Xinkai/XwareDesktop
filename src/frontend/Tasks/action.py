# -*- coding: utf-8 -*-

import logging
from launcher import app

from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal

from enum import IntEnum, unique
import collections
import sys
from urllib import parse

from utils import misc
from .mimeparser import UrlExtractor
from .watchers.clipboard import ClipboardWatcher
from .watchers.commandline import CommandlineWatcher


Batch = collections.namedtuple("UnpackedBatch", ["isLocalBt", "urls"])


@unique
class TaskCreationType(IntEnum):
    Normal = 0
    LocalTorrent = 1


class TaskCreation(object):
    def __init__(self, url = None, kind = None):
        self.url = url

        if kind is None:
            kind = TaskCreationType.Normal
        self.kind = kind

    def __repr__(self):
        return "{} <{}>".format(self.__class__.__name__, self.url)


class TaskCreationBatch(object):
    def __init__(self, tasks: list("TaskCreation")):
        self._tasks = tasks

    def unpack(self) -> Batch:
        taskUrls = list(map(lambda task: task.url, self._tasks))
        if self._tasks[0].kind == TaskCreationType.LocalTorrent:
            isLocalBt = True
        else:
            isLocalBt = False
        return Batch(isLocalBt = isLocalBt, urls = taskUrls)


class TaskCreationAgent(QObject):
    available = pyqtSignal()

    def __init__(self, parent = None):
        super().__init__(parent)
        self._queue = collections.deque()
        tasks = sys.argv[1:]
        if tasks:
            self.createTasksAction(tasks)

        self._urlExtractor = UrlExtractor(self)

        # load watchers
        self._clipboardWatcher = ClipboardWatcher(self)
        self._commandlineWatcher = CommandlineWatcher(self)

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
            combinedNormalTask = list(filter(lambda task: task.kind == TaskCreationType.Normal,
                                             alltasks))
            multipleLocalBtTasks = list(filter(lambda t: t.kind == TaskCreationType.LocalTorrent,
                                               alltasks))
        else:
            # else
            combinedNormalTask = [self._createTask()]
            multipleLocalBtTasks = []

        if combinedNormalTask:
            self._queueTaskCreation(TaskCreationBatch(combinedNormalTask))
        for singleLocalBtTask in multipleLocalBtTasks:  # because only 1 bt-task can be added once.
            self._queueTaskCreation(TaskCreationBatch([singleLocalBtTask]))

    def _queueTaskCreation(self, what: TaskCreationBatch):
        self._queue.append(what)
        self.available.emit()

    def dequeue(self):
        return self._queue.popleft()

    @staticmethod
    def _filterInvalidTasks(tasks) -> list("TaskCreation"):
        # remove those urls which were not recognized by self._createTask
        return list(filter(lambda t: t is not None, tasks))

    @staticmethod
    def _createTask(taskUrl: str = None) -> TaskCreation:
        if taskUrl is None:
            return TaskCreation()

        if taskUrl.startswith("file://"):
            taskUrl = taskUrl[len("file://"):]

        parsed = parse.urlparse(taskUrl)
        if parsed.scheme in ("thunder", "flashget", "qqdl"):
            url = misc.decodePrivateLink(taskUrl)
            return TaskCreation(url)

        elif parsed.scheme == "":
            if parsed.path.endswith(".torrent"):
                return TaskCreation(taskUrl, kind = TaskCreationType.LocalTorrent)

        elif parsed.scheme in ("http", "https", "ftp", "magnet", "ed2k"):
            return TaskCreation(taskUrl)
