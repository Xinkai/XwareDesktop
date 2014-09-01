# -*- coding: utf-8 -*-

import logging
from launcher import app

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


def _getFilenameFromED2K(url: (str, "netloc")):
    assert url[:6] == "|file|"
    url = url[6:]
    return parse.unquote(url[:url.index("|")])


def _getFilenameFromUrl(url: "ParseResult.path"):
    return parse.unquote(url[url.rindex("/") + 1:])


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

        self.url = url
        self._name = None
        self._name_user = None
        self.path = None
        self.kind = None
        if path.endswith(".torrent"):
            if scheme == "":
                self.kind = TaskCreationType.LocalTorrent
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
    def name(self):
        if self._name_user is not None:
            return self._name_user
        if self._name is not None:
            return self._name
        if self.kind == TaskCreationType.Emule:
            return _getFilenameFromED2K(self.parsed.netloc)
        if self.kind == TaskCreationType.Normal:
            return _getFilenameFromUrl(self.parsed.path)

    @name.setter
    def name(self, value):
        self._name_user = value

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
