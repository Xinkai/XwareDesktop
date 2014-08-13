# -*- coding: utf-8 -*-

import asyncio
import base64
from concurrent.futures import ThreadPoolExecutor
import json
import threading
import uuid
import websockets

from PyQt5.QtCore import QObject, pyqtProperty, pyqtSlot, pyqtSignal

from .definitions import Aria2TaskClass, Aria2Method
from .map import TaskMap


def _getShortName(name: str) -> str:
    # Takes a method name "aria2.addUri", returns "addUri"
    # Takes a response id "<uuid>.addUri", returns "addUri"
    # Takes a notification method name "aria2.onDownloadComplete", returns "onDownloadComplete"
    return name.split(".")[1]


def _fileEncode(f: "maybe a file-like object") -> str:
    if hasattr(f, "read") and hasattr(f, "write"):
        return base64.b64encode(f.read())
    else:
        return f


class _Callable(dict):
    def __init__(self, method: Aria2Method, *params):
        super().__init__()
        assert method in Aria2Method

        if method == Aria2Method.MultiCall:
            for i, callable_ in enumerate(params):
                assert isinstance(callable_, self.__class__)
                assert callable_["method"] != Aria2Method.MultiCall
                callable_["methodName"] = callable_.pop("method")
        else:
            params = list(map(_fileEncode, params))

        self["method"] = method.value
        self["params"] = params

    def toString(self):
        shortName = _getShortName(self["method"])
        self["id"] = "{uuid}.{shortName}".format(shortName = shortName,
                                                 uuid = uuid.uuid4().hex)
        self["jsonrpc"] = "2.0"
        return json.dumps(self)


class Aria2Adapter(QObject):
    initialized = pyqtSignal()
    statPolled = pyqtSignal()

    def __init__(self, adapterConfig = None, parent = None):
        super().__init__(parent)
        self._adapterConfig = adapterConfig
        self._ws = None

        self.maps = (
            TaskMap(self, Aria2TaskClass.Active),
            TaskMap(self, Aria2TaskClass.Waiting),
            TaskMap(self, Aria2TaskClass.Stopped),
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
            data = json.loads(msg)
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
        payload = callable_.toString()
        yield from self._ws.send(payload)

    def _callExternal(self, callable_: _Callable):
        asyncio.async(self._call(callable_))

    def do_createTask(self, url):
        self._loop.call_soon_threadsafe(self._callExternal, _Callable(Aria2Method.AddUri, [url]))

    @asyncio.coroutine
    def _cb_tellActive(self, result):
        self.maps[Aria2TaskClass.Active].updateData(result)

    @asyncio.coroutine
    def _cb_tellWaiting(self, result):
        self.maps[Aria2TaskClass.Waiting].updateData(result)

    @asyncio.coroutine
    def _cb_tellStopped(self, result):
        self.maps[Aria2TaskClass.Stopped].updateData(result)

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

    @asyncio.coroutine
    def _cb_getGlobalStat(self, result):
        self._dlSpeed = int(result["downloadSpeed"])
        self._ulSpeed = int(result["uploadSpeed"])
        # TODO: waiting, stopped, stoppedtotal, active
        self.statPolled.emit()
