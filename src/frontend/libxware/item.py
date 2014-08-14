# -*- coding: utf-8 -*-

from launcher import app
from PyQt5.QtCore import pyqtProperty, pyqtSignal, QObject
from datetime import datetime

from models.ProxyModel import TaskClass

_SPEED_SAMPLE_COUNT = 50


class VipChannel(QObject):
    updated = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self._type = None
        self._size = None
        self._speed = None
        self._speeds = [0] * _SPEED_SAMPLE_COUNT
        self._state = None
        self._available = None
        self._errorCode = None

    @pyqtProperty(int, notify = updated)
    def type(self):
        return self._type

    @pyqtProperty(int, notify = updated)
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
        return self._state

    @pyqtProperty(int, notify = updated)
    def available(self):
        return self._available

    @pyqtProperty(int, notify = updated)
    def errorCode(self):
        return self._errorCode

    def update(self, data):
        self._type = data.get("type")
        self._size = data.get("dlBytes")
        self.speed = data.get("speed")
        self._state = data.get("opened")
        self._available = data.get("available")
        self._errorCode = data.get("failCode")
        self.updated.emit()


class LixianChannel(QObject):
    updated = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self._state = None
        self._speed = None
        self._speeds = [0] * _SPEED_SAMPLE_COUNT
        self._size = None
        self._serverSpeed = None
        self._serverProgress = None
        self._errorCode = None

    @pyqtProperty(int, notify = updated)
    def state(self):
        return self._state

    @pyqtProperty(int, notify = updated)
    def speed(self):
        return self._speed

    @speed.setter
    def speed(self, value):
        self._speed = value
        self._speeds = self.speeds[1:] + [value]

    @pyqtProperty("QList<int>", notify = updated)
    def speeds(self):
        return self._speeds

    @pyqtProperty(int, notify = updated)
    def size(self):
        return self._size

    @pyqtProperty(int, notify = updated)
    def serverSpeed(self):
        return self._serverSpeed

    @pyqtProperty(int, notify = updated)
    def serverProgress(self):
        return self._serverProgress

    @pyqtProperty(int, notify = updated)
    def errorCode(self):
        return self._errorCode

    def update(self, data):
        self._state = data.get("state")
        self.speed = data.get("speed")
        self._size = data.get("dlBytes")
        self._serverSpeed = data.get("serverSpeed")
        self._serverProgress = data.get("serverProgress")
        self._errorCode = data.get("failCode")
        self.updated.emit()


class XwareTaskItem(QObject):
    initialized = pyqtSignal()
    updated = pyqtSignal()
    errorOccurred = pyqtSignal()

    def __init__(self, *, adapter):
        super().__init__(None)
        self._initialized = False
        self._adapter = adapter
        self._namespace = self._adapter.namespace
        self._klass = TaskClass.INVALID

        self._id = None
        self._name = None
        self._speed = None
        self._speeds = [0] * _SPEED_SAMPLE_COUNT
        self._progress = None
        self._creationTime = None
        self._runningTime = None
        self._remainingTime = None
        self._completionTime = None
        self._state = None
        self._path = None
        self._size = None
        self._errorCode = None

        self._vipChannel = VipChannel(self)
        self._lixianChannel = LixianChannel(self)

        self.moveToThread(self._adapter.thread())
        self.setParent(self._adapter)

    @pyqtProperty(int, notify = initialized)
    def realid(self):
        return self._id

    @pyqtProperty(str, notify = initialized)
    def id(self):
        return self.namespace + "|" + str(self.realid)

    @pyqtProperty(str, notify = initialized)
    def name(self):
        return self._name

    @pyqtProperty(int, notify = initialized)
    def creationTime(self):
        return self._creationTime

    @pyqtProperty(str, notify = initialized)
    def path(self):
        return self._path

    @pyqtProperty(str, notify = initialized)
    def namespace(self):
        return self._namespace

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
    def progress(self):
        return self._progress

    @pyqtProperty(int, notify = updated)
    def remainingTime(self):
        return self._remainingTime

    @pyqtProperty(int, notify = updated)
    def completionTime(self):
        return self._completionTime

    @pyqtProperty(int, notify = updated)
    def state(self):
        return self._state

    @pyqtProperty(int, notify = errorOccurred)
    def errorCode(self):
        return self._errorCode

    @pyqtProperty(QObject, notify = initialized)
    def vipChannel(self):
        return self._vipChannel

    @pyqtProperty(QObject, notify = initialized)
    def lixianChannel(self):
        return self._lixianChannel

    @property
    def fullpath(self):
        return self.path + self.name

    @pyqtProperty(int, notify = updated)
    def klass(self):
        # _klass is xware class[0-3],
        # return Xware Desktop task class
        return self._xwareClassToClass(self._klass)
        # Xware Local Control doesn't always return reliable state,
        # needs to use class directly

        # from .vanilla import TaskClass as XwareTaskClass
        # return {
        #     XwareTaskClass.DOWNLOADING: TaskClass.RUNNING,
        #     XwareTaskClass.WAITING: TaskClass.RUNNING,
        #     XwareTaskClass.STOPPED: TaskClass.RUNNING,
        #     XwareTaskClass.PAUSED: TaskClass.RUNNING,
        #     XwareTaskClass.FINISHED: TaskClass.COMPLETED,
        #     XwareTaskClass.FAILED: TaskClass.FAILED,
        #     XwareTaskClass.UPLOADING: TaskClass.RUNNING,
        #     XwareTaskClass.SUBMITTING: TaskClass.RUNNING,
        #     XwareTaskClass.DELETED: TaskClass.RECYCLED,
        #     XwareTaskClass.RECYCLED: TaskClass.RECYCLED,
        #     XwareTaskClass.SUSPENDED: TaskClass.RUNNING,
        #     XwareTaskClass.ERROR: TaskClass.FAILED,
        # }[self.state]

    @klass.setter
    def klass(self, value):
        oldClass = self.klass
        self._klass = value
        newClass = self._xwareClassToClass(value)
        if oldClass == newClass:
            return

        if newClass == TaskClass.COMPLETED:
            timestamp = datetime.timestamp(datetime.now())
            if 0 <= timestamp - self.completionTime <= 10:
                app.taskModel.taskCompleted.emit(self)

    @staticmethod
    def _xwareClassToClass(klass: int):
        return 1 << klass

    def update(self, data, klass):
        self.speed = data.get("speed")
        self._remainingTime = int(data.get("remainTime"))
        self._state = data.get("state")
        self._completionTime = data.get("completeTime")
        self._progress = data.get("progress")
        self._runningTime = data.get("downTime")

        self._vipChannel.update(data.get("vipChannel"))
        self._lixianChannel.update(data.get("lixianChannel"))

        if not self._initialized:
            self._id = data.get("id")
            self._name = data.get("name")
            self._creationTime = data.get("createTime")
            self._path = data.get("path")
            self._size = data.get("size")
            self._initialized = True
            self.initialized.emit()

        self.klass = klass
        self.updated.emit()
