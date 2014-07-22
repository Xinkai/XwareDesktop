# -*- coding: utf-8 -*-

from launcher import app

import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import threading, uuid

from models.ProxyModel import TaskClass
from utils.system import systemOpen, viewOneFile, viewMultipleFiles

from .vanilla import TaskState, XwareClient
from .vanilla import TaskClass as XwareTaskClass
from .map import Tasks

_POLLING_INTERVAL = 1


class XwareAdapter(object):
    _mapIds = None
    _ulSpeed = 0
    _dlSpeed = 0

    def __init__(self, clientOptions):
        super().__init__()
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

    def updateOptions(self, clientOptions):
        self._xwareClient.updateOptions(clientOptions)

    @staticmethod
    def getTaskClass(data):
        d = {
            XwareTaskClass.DOWNLOADING: TaskClass.RUNNING,
            XwareTaskClass.WAITING: TaskClass.RUNNING,
            XwareTaskClass.STOPPED: TaskClass.RUNNING,
            XwareTaskClass.PAUSED: TaskClass.RUNNING,
            XwareTaskClass.FINISHED: TaskClass.COMPLETED,
            XwareTaskClass.FAILED: TaskClass.FAILED,
            XwareTaskClass.UPLOADING: TaskClass.RUNNING,
            XwareTaskClass.SUBMITTING: TaskClass.RUNNING,
            XwareTaskClass.DELETED: TaskClass.RECYCLED,
            XwareTaskClass.RECYCLED: TaskClass.RECYCLED,
            XwareTaskClass.SUSPENDED: TaskClass.RUNNING,
            XwareTaskClass.ERROR: TaskClass.FAILED,
        }
        return d[data["state"]]

    # =========================== PUBLIC ===========================
    @asyncio.coroutine
    def main(self):
        # Entry point of the thread "XwareAdapterEventLoop"
        # main() handles non-stop polling

        runningId = yield from app.taskModel.taskManager.appendMap(
            Tasks(self.namespace, TaskState.RUNNING))
        completedId = yield from app.taskModel.taskManager.appendMap(
            Tasks(self.namespace, TaskState.COMPLETED))
        recycledId = yield from app.taskModel.taskManager.appendMap(
            Tasks(self.namespace, TaskState.RECYCLED))
        failedOnSubmissionId = yield from app.taskModel.taskManager.appendMap(
            Tasks(self.namespace, TaskState.FAILED_ON_SUBMISSION))
        self._mapIds = (runningId, completedId, recycledId, failedOnSubmissionId)

        while True:
            self._loop.call_soon(self.get_getsysinfo)
            self._loop.call_soon(self.get_list, TaskState.RUNNING)
            self._loop.call_soon(self.get_list, TaskState.COMPLETED)
            self._loop.call_soon(self.get_list, TaskState.RECYCLED)
            self._loop.call_soon(self.get_list, TaskState.FAILED_ON_SUBMISSION)
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

    def _donecb_get_list(self, state, future):
        result = future.result()

        if state == TaskState.RUNNING:
            self.ulSpeed = result["upSpeed"]
            self.dlSpeed = result["dlSpeed"]
        mapId = self._mapIds[int(state)]
        app.taskModel.taskManager.updateMap(mapId, result["tasks"])

    def _donecb_get_settings(self, future):
        pass

    def do_pauseTasks(self, tasks, options):
        taskIds = map(lambda t: t["id"], tasks)
        self._loop.call_soon_threadsafe(self.post_pause, taskIds)

    def do_startTasks(self, tasks, options):
        taskIds = map(lambda t: t["id"], tasks)
        self._loop.call_soon_threadsafe(self.post_start, taskIds)

    def do_openLixianChannel(self, task, enable: bool):
        taskId = task["id"]
        self._loop.call_soon_threadsafe(self.post_openLixianChannel, taskId, enable)

    def do_openVipChannel(self, task):
        taskId = task["id"]
        self._loop.call_soon_threadsafe(self.post_openVipChannel, taskId)

    @staticmethod
    def do_systemOpen(task):
        filename = task["path"] + task["name"]
        systemOpen(filename)

    @staticmethod
    def do_viewOneTask(task):
        filename = task["path"] + task["name"]
        viewOneFile(filename)

    @staticmethod
    def do_viewMultipleTasks(tasks):
        filenames = map(lambda t: t["path"] + t["name"], tasks)
        viewMultipleFiles(filenames)


class XwareAdapterThread(threading.Thread):
    _loop = None
    _loop_executor = None
    _adapter = None

    def __init__(self, options):
        super().__init__(name = "XwareAdapterEventLoop", daemon = True)
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
