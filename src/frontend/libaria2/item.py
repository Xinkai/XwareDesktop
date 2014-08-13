# -*- coding: utf-8 -*-

from launcher import app
from PyQt5.QtCore import pyqtProperty, pyqtSignal, QObject

import os

from models.TaskModel import TaskClass
_SPEED_SAMPLE_COUNT = 50


class Aria2TaskItem(QObject):
    initialized = pyqtSignal()
    updated = pyqtSignal()

    def __init__(self, *, adapter):
        super().__init__(None)
        self._initialized = False
        self._adapter = adapter

        self._gid = None
        self._size = 0
        self._dlsize = 0
        self._ulsize = 0
        self._status = None
        self._speed = 0
        self._speeds = [0] * _SPEED_SAMPLE_COUNT
        self._path = None
        self._files = []
        self._bittorrent = None

        self.moveToThread(self._adapter.thread())
        self.setParent(self._adapter)

    @pyqtProperty(str, notify = initialized)
    def realid(self):
        return self._gid

    @pyqtProperty(str, notify = initialized)
    def id(self):
        return self.namespace + "|" + self.realid

    @pyqtProperty(int, notify = initialized)
    def size(self):
        return self._size

    @pyqtProperty(int, notify = updated)
    def speed(self):
        return self._speed

    @speed.setter
    def speed(self, value):
        self._speed = value
        self._speeds = self._speeds[1:] + [value]

    @pyqtProperty("QList<int>", notify = updated)
    def speeds(self):
        return self._speeds

    @pyqtProperty(int, notify = updated)
    def klass(self):
        return {
            "active": TaskClass.RUNNING,
            "waiting": TaskClass.RUNNING,
            "paused": TaskClass.RUNNING,
            "error": TaskClass.FAILED,
            "complete": TaskClass.COMPLETED,
            "removed": TaskClass.RECYCLED,
        }[self._status]

    @pyqtProperty(int, notify = initialized)
    def creationTime(self):
        return 0  # TODO: Aria2 doesn't provide this information

    @pyqtProperty(int, notify = initialized)
    def completionTime(self):
        return 0  # TODO: Aria2 doesn't provide this information

    @pyqtProperty(int, notify = updated)
    def remainingTime(self):
        return 0  # TODO

    @pyqtProperty(str, notify = initialized)
    def path(self):
        return self._path

    @pyqtProperty(int, notify = updated)
    def progress(self):
        try:
            return (self._dlsize / self._size) * 10000
        except ZeroDivisionError:
            return 0

    @pyqtProperty(str, notify = initialized)
    def name(self):
        if not self._files:
            return "ERROR"

        if self._bittorrent:
            return self._bittorrent["info"]["name"]

        if len(self._files) == 1:
            return os.path.basename(self._files[0]["path"])
        else:
            raise NotImplementedError()

    @pyqtProperty(str, notify = initialized)
    def fullpath(self):
        if len(self._files) == 1:
            return self._files[0]["path"]
        else:
            raise NotImplementedError()

    def update(self, data, klass):
        self.speed = int(data.get("downloadSpeed", 0))
        self._status = data["status"]
        self._ulsize = int(data.get("uploadLength"))
        self._dlsize = int(data.get("completedLength"))
        self._bittorrent = data.get("bittorrent")

        if not self._initialized:
            self._gid = data.get("gid")
            self._path = data.get("dir")
            self._size = int(data.get("totalLength"))
            self._files = data.get("files")
            self._initialized = True
            self.initialized.emit()

        self.updated.emit()

