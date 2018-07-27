# -*- coding: utf-8 -*-

import logging

from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal

from enum import Enum, unique
import collections
import sys
from urllib import parse
from urllib.parse import ParseResult

from utils import misc
from .mimeparser import UrlExtractor
from .watchers.clipboard import ClipboardWatcher
from .watchers.commandline import CommandlineWatcher


@unique
class TaskCreationType(Enum):
    Empty = 0
    Normal = 1
    Emule = 2
    LocalTorrent = 3
    Magnet = 4
    MetaLink = 5
    RemoteTorrent = 6


class TaskCreation(object):
    def __init__(self, parsed: ParseResult = None):
        self.parsed = parsed
        if parsed is None:
            self.kind = TaskCreationType.Empty
            self.url = None
            return

        path = parsed.path
        scheme = parsed.scheme

        url = parsed.geturl()

        # subtaskInfo is set by Model
        self.subtaskInfo = []

        self.url = url
        self.path = None
        self.kind = None
        if path.endswith(".torrent"):
            if scheme == "":
                self.kind = TaskCreationType.LocalTorrent
                return
            elif scheme in ("http", "https", "ftp"):
                self.kind = TaskCreationType.RemoteTorrent
                return

        if path.endswith(".metalink") or path.endswith(".meta4"):
            if scheme in ("http", "https", "ftp"):
                self.kind = TaskCreationType.MetaLink

        elif scheme == "ed2k":
            self.kind = TaskCreationType.Emule

        elif scheme == "magnet":
            self.kind = TaskCreationType.Magnet

        elif scheme in ("http", "https", "ftp"):
            self.kind = TaskCreationType.Normal

    @property
    def isValid(self) -> bool:
        if not self.kind:
            # scheme is not recognized
            return False

        if not self.parsed:
            # parsed is None
            return False

        if (not self.parsed.path) and (self.kind is not TaskCreationType.Magnet):
            # "http://domain."
            return False

        if not self.parsed.netloc:
            if self.parsed.scheme == "":
                return True
            elif self.parsed.scheme == "magnet":
                return True
            return False
        return True

    def __repr__(self):
        return "{} <{}>".format(self.__class__.__name__, self.url)


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
        creations = []
        if taskUrls:
            for taskUrl in taskUrls:
                creations.append(self._createTask(taskUrl))
        else:
            creations.append(self._createTask())

        for creation in creations:
            if creation is not None:
                self._queueTaskCreation(creation)

    def _queueTaskCreation(self, what: TaskCreation):
        self._queue.append(what)
        self.available.emit()

    def dequeue(self):
        return self._queue.popleft()

    @staticmethod
    def _createTask(taskUrl: str = None) -> TaskCreation:
        if taskUrl is None:
            return TaskCreation()

        if taskUrl.startswith("file://"):
            taskUrl = taskUrl[len("file://"):]

        parsed = parse.urlparse(taskUrl)
        if parsed.scheme in ("thunder", "flashget", "qqdl"):
            taskUrl = misc.decodePrivateLink(taskUrl)
            parsed = parse.urlparse(taskUrl)

        return TaskCreation(parsed)
