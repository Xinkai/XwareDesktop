# -*- coding: utf-8 -*-

from launcher import app
from PyQt5.QtCore import pyqtProperty, pyqtSignal, QObject

import os

from models.TaskModel import TaskClass, TaskState
from .definitions import Aria2TaskState
from utils.misc import pathSplit

_SPEED_SAMPLE_COUNT = 50


class Aria2TaskItem(QObject):
    initialized = pyqtSignal()
    updated = pyqtSignal()

    def __init__(self, *, adapter):
        super().__init__(None)
        self._initialized = False
        self._adapter = adapter
        self._namespace = self._adapter.namespace
        self._klass = None

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

        self._creationTime = 0
        self._completionTime = 0
        self._isDeletionPending = False

        self.moveToThread(self._adapter.thread())
        self.setParent(self._adapter)

    @pyqtProperty(str, notify = initialized)
    def realid(self):
        return self._gid

    @pyqtProperty(str, notify = initialized)
    def id(self):
        return self.namespace + "|" + self.realid

    @pyqtProperty(str, notify = initialized)
    def namespace(self):
        return self._namespace

    @pyqtProperty("ulong", notify = initialized)
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
    def state(self):
        result = {
            Aria2TaskState.Active.value: TaskState.Downloading,
            Aria2TaskState.Waiting.value: TaskState.Waiting,
            Aria2TaskState.Paused.value: TaskState.Paused,
            Aria2TaskState.Error.value: TaskState.Failed,
            Aria2TaskState.Complete.value: TaskState.Completed,
            Aria2TaskState.Removed.value: TaskState.Removed,
        }.get(self._status, TaskState.Unrecognized)
        if result in (TaskState.Downloading, TaskState.Paused):
            if self._dlsize == self._size:
                result = TaskState.Completed
        return result

    @pyqtProperty(int, notify = updated)
    def klass(self):
        result = {
            Aria2TaskState.Active.value: TaskClass.RUNNING,
            Aria2TaskState.Waiting.value: TaskClass.RUNNING,
            Aria2TaskState.Paused.value: TaskClass.RUNNING,
            Aria2TaskState.Error.value: TaskClass.FAILED,
            Aria2TaskState.Complete.value: TaskClass.COMPLETED,
            Aria2TaskState.Removed.value: TaskClass.RECYCLED,
        }.get(self._status, TaskClass.INVALID)
        if result == TaskClass.RUNNING:
            if self._dlsize == self._size:
                # Seeding
                result = TaskClass.COMPLETED
        return result

    @pyqtProperty(int, notify = initialized)
    def creationTime(self):
        if self._creationTime:
            return self._creationTime

        try:
            self._creationTime = int(os.stat(self.fullpath).st_ctime)
        except FileNotFoundError:
            self._creationTime = 0
        return self._creationTime

    @pyqtProperty(int, notify = initialized)
    def completionTime(self):
        if self._dlsize != self._size:
            return 0

        if self._completionTime:
            return self._completionTime
        try:
            self._completionTime = int(os.stat(self.fullpath).st_mtime)
        except FileNotFoundError:
            self._completionTime = 0
        return self._completionTime

    @pyqtProperty(int, notify = updated)
    def remainingTime(self):
        remainingSize = self._size - self._dlsize
        try:
            return int(remainingSize / self._speed)
        except ZeroDivisionError:
            return 1 << 32

    @pyqtProperty(str, notify = initialized)
    def path(self):
        return self._path

    @pyqtProperty(int, notify = updated)
    def progress(self):
        try:
            return (self._dlsize / self._size) * 10000
        except ZeroDivisionError:
            return 10000

    @pyqtProperty(str, notify = initialized)
    def name(self):
        if not self._files:
            raise ValueError()

        if len(self._files) == 1:
            return os.path.basename(self._files[0]["path"])
        else:
            if self._bittorrent:
                return self._bittorrent["info"]["name"]
            else:
                # when the torrent file/aria2 control file is gone
                # need to calculate fullpath of the base dir.
                pathParts = pathSplit(self._path)  # "home", "user", "Downloads"
                fileParts = pathSplit(self._files[0]["path"])  # "home", "user", "Downloads", "foo"
                return fileParts[len(pathParts)]

    @pyqtProperty(str, notify = initialized)
    def fullpath(self):
        if len(self._files) == 1:
            return self._files[0]["path"]
        else:
            return os.path.join(self._path, self.name)

    @pyqtProperty(bool, notify = updated)
    def isDeletionPending(self):
        return self._isDeletionPending

    @isDeletionPending.setter
    def isDeletionPending(self, value):
        self._isDeletionPending = value

    def update(self, data, klass):
        self._klass = klass
        self.speed = int(data.get("downloadSpeed", 0))
        self._ulsize = int(data.get("uploadLength"))
        self._dlsize = int(data.get("completedLength"))
        self._bittorrent = data.get("bittorrent")

        if (not self._initialized) or (self._status is not data["status"]):
            self._status = data["status"]
            self._gid = data.get("gid")
            self._path = data.get("dir")
            self._size = int(data.get("totalLength"))
            self._files = data.get("files")
            self._initialized = True
            self.initialized.emit()

        self.updated.emit()
