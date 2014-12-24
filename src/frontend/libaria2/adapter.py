# -*- coding: utf-8 -*-

import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
import threading
import uuid
import websockets

from PyQt5.QtCore import QObject, pyqtProperty, pyqtSlot, pyqtSignal

from Tasks.action import TaskCreation, TaskCreationType
from models.KlassMap import KlassMap
from .definitions import Aria2TaskClass, Aria2Method
from .map import TaskMap


def _getShortName(name: str) -> str:
    # Takes a method name "aria2.addUri", returns "addUri"
    # Takes a response id "<uuid>.addUri", returns "addUri"
    # Takes a notification method name "aria2.onDownloadComplete", returns "onDownloadComplete"
    return name.split(".")[1]


class _Callable(dict):
    def __init__(self, method: Aria2Method, *params):
        super().__init__()
        assert method in Aria2Method

        if method == Aria2Method.MultiCall:
            for i, callable_ in enumerate(params):
                assert isinstance(callable_, self.__class__)
                assert callable_["method"] != Aria2Method.MultiCall

        self["method"] = method.value
        self["params"] = list(params)
        self["id"] = "{uuid}.{shortName}".format(shortName = _getShortName(self["method"]),
                                                 uuid = uuid.uuid4().hex)
        self["jsonrpc"] = "2.0"

    def toString(self, token = None):
        if self["method"] == Aria2Method.MultiCall.value:
            # add token to individual calls
            if token:
                for call in self["params"]:
                    call["params"].insert(0, "token:" + token)

            return json.dumps(self["params"])
        else:
            if token:
                self["params"].insert(0, "token:" + token)

            return json.dumps(self)


class Aria2Adapter(QObject):
    initialized = pyqtSignal()
    statPolled = pyqtSignal()

    def __init__(self, *, adapterConfig, taskModel, parent = None):
        super().__init__(parent)
        self._adapterConfig = adapterConfig
        self._ws = None

        self.klassMap = KlassMap(adapter = self, namespace = self.namespace, taskModel = taskModel)
        self.klassMap.addTaskMap(
            TaskMap(klass = Aria2TaskClass.Active)
        )
        self.klassMap.addTaskMap(
            TaskMap(klass = Aria2TaskClass.Waiting)
        )
        self.klassMap.addTaskMap(
            TaskMap(klass = Aria2TaskClass.Stopped)
        )

        # Stats
        self._ulSpeed = 0
        self._dlSpeed = 0
        self._activeCount = 0
        self._waitingCount = 0
        self._stoppedCount = 0
        self._stoppedTotalCount = 0

        self._ids = {}
        self._loop = None
        self._loop_executor = None
        self._loop_thread = threading.Thread(daemon = True,
                                             target = self._startEventLoop,
                                             name = adapterConfig.name)

    def start(self):
        self._loop_thread.start()

    def _startEventLoop(self):
        self._loop = asyncio.new_event_loop()
        self._loop.set_debug(True)
        self._loop_executor = ThreadPoolExecutor(max_workers = 1)
        self._loop.set_default_executor(self._loop_executor)
        asyncio.events.set_event_loop(self._loop)
        asyncio.async(self.main())
        self._loop.run_forever()

    def updateOptions(self, options):
        self._options.update(options)

    def _ready(self):
        if not self._ws:
            return False
        return self._ws.open

    @pyqtProperty(str, notify = initialized)
    def name(self):
        return self._adapterConfig["name"]

    @pyqtProperty(str, notify = initialized)
    def connection(self):
        return self._adapterConfig["connection"]

    @pyqtProperty(str, notify = initialized)
    def namespace(self):
        return "aria2-" + self._adapterConfig.name[len("adapter-"):]

    @asyncio.coroutine
    def main(self):
        asyncio.async(self._getMessage())  # It can handle reconnect
        while True:
            try:
                self._ws = yield from websockets.client.connect(
                    self._adapterConfig["connection"]
                )
            except ConnectionRefusedError:
                yield from asyncio.sleep(1)
                continue

            while True:
                if not self._ready():
                    break

                asyncio.async(self._call(_Callable(Aria2Method.GetGlobalStat)))
                asyncio.async(self._call(_Callable(Aria2Method.TellActive)))
                asyncio.async(self._call(_Callable(Aria2Method.TellWaiting, 0, 100000)))
                asyncio.async(self._call(_Callable(Aria2Method.TellStopped, 0, 100000)))
                yield from asyncio.sleep(1)

    @asyncio.coroutine
    def _getMessage(self):
        while True:
            if not self._ready():
                yield from asyncio.sleep(1)  # try again in 1 sec
                continue

            msg = yield from self._ws.recv()
            if not msg:
                continue  # disconnected
            datas = json.loads(msg)

            # make a single call's response look like being part of a batch call
            if not isinstance(datas, list):
                datas = (datas,)

            for data in datas:
                assert data["jsonrpc"] == "2.0"
                if "error" in data:
                    print("Error Handling", data)  # TODO
                else:
                    id_ = data.get("id", None)
                    if id_:
                        # response
                        shortName = _getShortName(id_)
                        result = data["result"]
                    else:
                        # notifications
                        shortName = _getShortName(data["method"])
                        result = data["params"]

                    cb = getattr(self, "_cb_" + shortName, None)
                    if cb:
                        assert asyncio.iscoroutinefunction(cb)
                        yield from cb(result)

    @asyncio.coroutine
    def _call(self, callable_: _Callable):
        assert isinstance(callable_, _Callable)
        additionals = dict()
        if "rpc-secret" in self._adapterConfig:
            additionals["token"] = self._adapterConfig["rpc-secret"]
        payload = callable_.toString(**additionals)
        yield from self._ws.send(payload)

    def _callFromExternal(self, callable_: _Callable):
        self._loop.call_soon_threadsafe(asyncio.async, self._call(callable_))

    def do_createTask(self, creation: TaskCreation):
        url = [creation.url]
        options = dict(dir = creation.path)

        if creation.kind in (TaskCreationType.Normal,):
            # see if need to override filename
            fileInfo = creation.subtaskInfo[0]
            if fileInfo.name_userset:
                options["out"] = fileInfo.name

            self._callFromExternal(
                _Callable(Aria2Method.AddUri, url, options)
            )
            return True
        elif creation.kind == TaskCreationType.Magnet:
            self._callFromExternal(
                _Callable(Aria2Method.AddUri, url, dict())
            )
            return True

        return False

    def do_getFiles(self, gid):
        self._callFromExternal(_Callable(Aria2Method.GetFiles, gid))

    def do_delTasks(self, tasks, options):
        taskIds = map(lambda t: t.realid, tasks)
        calls = map(lambda gid: _Callable(Aria2Method.RemoveDownloadResult, gid), taskIds)
        delMultiple = _Callable(Aria2Method.MultiCall, *calls)
        # TODO: aria2 don't remove files from filesystem.
        self._callFromExternal(delMultiple)

    @asyncio.coroutine
    def _cb_tellActive(self, result):
        self.klassMap.klass(Aria2TaskClass.Active).updateData(result)

    @asyncio.coroutine
    def _cb_tellWaiting(self, result):
        self.klassMap.klass(Aria2TaskClass.Waiting).updateData(result)

    @asyncio.coroutine
    def _cb_tellStopped(self, result):
        self.klassMap.klass(Aria2TaskClass.Stopped).updateData(result)

    @asyncio.coroutine
    def _cb_getGlobalOption(self, result):
        pass

    @asyncio.coroutine
    def _cb_getFiles(self, result):
        print("_cb_getFiles", result)

    @asyncio.coroutine
    def _cb_onDownloadStart(self, event):
        print("_cb_onDownloadComplete", event)

    @asyncio.coroutine
    def _cb_onDownloadPause(self, event):
        print("_cb_onDownloadPause", event)

    @asyncio.coroutine
    def _cb_onDownloadStop(self, event):
        print("_cb_onDownloadStop", event)

    @asyncio.coroutine
    def _cb_onDownloadComplete(self, event):
        print("_cb_onDownloadComplete", event)

    @asyncio.coroutine
    def _cb_onDownloadError(self, event):
        print("_cb_onDownloadError", event)

    @asyncio.coroutine
    def _cb_onBtDownloadComplete(self, event):
        print("_cb_onBtDownloadComplete", event)

    # Stats
    @pyqtProperty(int, notify = statPolled)
    def dlSpeed(self):
        return self._dlSpeed

    @pyqtProperty(int, notify = statPolled)
    def ulSpeed(self):
        return self._ulSpeed

    @pyqtProperty(int, notify = statPolled)
    def runningTaskCount(self):
        return 0  # TODO

    @asyncio.coroutine
    def _cb_getGlobalStat(self, result):
        self._dlSpeed = int(result["downloadSpeed"])
        self._ulSpeed = int(result["uploadSpeed"])
        # TODO: waiting, stopped, stoppedtotal, active
        self.statPolled.emit()
