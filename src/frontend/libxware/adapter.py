# -*- coding: utf-8 -*-

from launcher import app

import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import threading, uuid

from PyQt5.QtCore import QObject, pyqtSignal, pyqtProperty
from .vanilla import TaskClass, XwareClient, Settings
from .map import Tasks

_POLLING_INTERVAL = 1


class XwareSettings(QObject):
    updated = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self._settings = None

    @pyqtProperty(int, notify = updated)
    def downloadSpeedLimit(self):
        return self._settings.downloadSpeedLimit

    @pyqtProperty(int, notify = updated)
    def uploadSpeedLimit(self):
        return self._settings.uploadSpeedLimit

    @pyqtProperty(int, notify = updated)
    def slStartTime(self):
        return self._settings.slStartTime

    @pyqtProperty(int, notify = updated)
    def slEndTime(self):
        return self._settings.slEndTime

    @pyqtProperty(int, notify = updated)
    def maxRunTaskNumber(self):
        return self._settings.maxRunTaskNumber

    @pyqtProperty(int, notify = updated)
    def autoOpenLixian(self):
        return self._settings.autoOpenLixian

    @pyqtProperty(int, notify = updated)
    def autoOpenVip(self):
        return self._settings.autoOpenVip

    @pyqtProperty(int, notify = updated)
    def autoDlSubtitle(self):
        return self._settings.autoDlSubtitle

    def update(self, settings: Settings):
        self._settings = settings
        self.updated.emit()


class XwareAdapter(QObject):
    update = pyqtSignal(int, list)

    def __init__(self, clientOptions):
        super().__init__()
        self._mapIds = None
        self._ulSpeed = 0
        self._dlSpeed = 0
        self._xwareSettings = XwareSettings(self)
        self._loop = asyncio.get_event_loop()
        self._uuid = uuid.uuid1().hex
        self._xwareClient = XwareClient(clientOptions)

    @property
    def namespace(self):
        return "xware-" + self._uuid

    @property
    def ulSpeed(self):
        return self._ulSpeed

    @ulSpeed.setter
    def ulSpeed(self, value):
        if value != self._ulSpeed:
            self._ulSpeed = value
            app.adapterManager.ulSpeedChanged.emit()

    @property
    def dlSpeed(self):
        return self._dlSpeed

    @dlSpeed.setter
    def dlSpeed(self, value):
        if value != self._dlSpeed:
            self._dlSpeed = value
            app.adapterManager.dlSpeedChanged.emit()

    @property
    def backendSettings(self):
        return self._xwareSettings

    def updateOptions(self, clientOptions):
        self._xwareClient.updateOptions(clientOptions)

    # =========================== PUBLIC ===========================
    @asyncio.coroutine
    def main(self):
        # Entry point of the thread "XwareAdapterEventLoop"
        # main() handles non-stop polling

        runningId = yield from app.taskModel.taskManager.appendMap(
            Tasks(self, TaskClass.RUNNING))
        completedId = yield from app.taskModel.taskManager.appendMap(
            Tasks(self, TaskClass.COMPLETED))
        recycledId = yield from app.taskModel.taskManager.appendMap(
            Tasks(self, TaskClass.RECYCLED))
        failedOnSubmissionId = yield from app.taskModel.taskManager.appendMap(
            Tasks(self, TaskClass.FAILED_ON_SUBMISSION))
        self._mapIds = (runningId, completedId, recycledId, failedOnSubmissionId)

        while True:
            self._loop.call_soon(self.get_getsysinfo)
            self._loop.call_soon(self.get_list, TaskClass.RUNNING)
            self._loop.call_soon(self.get_list, TaskClass.COMPLETED)
            self._loop.call_soon(self.get_list, TaskClass.RECYCLED)
            self._loop.call_soon(self.get_list, TaskClass.FAILED_ON_SUBMISSION)
            self._loop.call_soon(self.get_settings)

            yield from asyncio.sleep(_POLLING_INTERVAL)

    # =========================== META-PROGRAMMING MAGICS ===========================
    def __getattr__(self, name):
        if name.startswith("get_") or name.startswith("post_"):
            def method(*args):
                clientMethod = getattr(self._xwareClient, name)(*args)
                clientMethod = asyncio.async(clientMethod)

                donecb = getattr(self, "_donecb_" + name, None)
                if donecb:
                    curried = partial(donecb, *args)
                    clientMethod.add_done_callback(curried)
            setattr(self, name, method)
            return method
        raise AttributeError("XwareAdapter doesn't have a {name}.".format(**locals()))

    def _donecb_get_getsysinfo(self, future):
        pass

    def _donecb_get_list(self, klass, future):
        result = future.result()

        if klass == TaskClass.RUNNING:
            self.ulSpeed = result["upSpeed"]
            self.dlSpeed = result["dlSpeed"]
        mapId = self._mapIds[int(klass)]
        self.update.emit(mapId, result["tasks"])

    def _donecb_get_settings(self, future):
        result = future.result()
        self._xwareSettings.update(result)

    def do_pauseTasks(self, tasks, options):
        taskIds = map(lambda t: t.realid, tasks)
        self._loop.call_soon_threadsafe(self.post_pause, taskIds)

    def do_startTasks(self, tasks, options):
        taskIds = map(lambda t: t.realid, tasks)
        self._loop.call_soon_threadsafe(self.post_start, taskIds)

    def do_openLixianChannel(self, taskItem, enable: bool):
        taskId = taskItem.realid
        self._loop.call_soon_threadsafe(self.post_openLixianChannel, taskId, enable)

    def do_openVipChannel(self, taskItem):
        taskId = taskItem.realid
        self._loop.call_soon_threadsafe(self.post_openVipChannel, taskId)


class XwareAdapterThread(threading.Thread):
    def __init__(self, options):
        super().__init__(name = "XwareAdapterEventLoop", daemon = True)
        self._loop = None
        self._loop_executor = None
        self._adapter = None
        self._options = options

    def run(self):
        self._loop = asyncio.new_event_loop()
        self._loop.set_debug(True)
        self._loop_executor = ThreadPoolExecutor(max_workers = 1)
        self._loop.set_default_executor(self._loop_executor)
        asyncio.events.set_event_loop(self._loop)

        self._adapter = XwareAdapter(self._options)
        app.adapterManager.registerAdapter(self._adapter)
        asyncio.async(self._adapter.main())
        self._loop.run_forever()
