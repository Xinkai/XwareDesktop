# -*- coding: utf-8 -*-

import asyncio
import base64
from concurrent.futures import ThreadPoolExecutor
import json
import threading
import uuid
import websockets

from PyQt5.QtCore import QObject, pyqtProperty, pyqtSlot, pyqtSignal

from enum import Enum, unique


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


@unique
class Aria2Method(Enum):
    AddUri = "aria2.addUri"
    AddTorrent = "aria2.addTorrent"
    AddMetaLink = "aria2.addMetalink"
    Remove = "aria2.remove"
    ForceRemove = "aria2.forceRemove"
    Pause = "aria2.pause"
    PauseAll = "aria2.pauseAll"
    ForcePause = "aria2.forcePause"
    ForcePauseAll = "aria2.forcePauseAll"
    Unpause = "aria2.unpause"
    UnpauseAll = "aria2.unpauseAll"
    TellStatus = "aria2.tellStatus"
    GetUris = "aria2.GetUris"
    GetFiles = "aria2.GetFiles"
    GetPeers = "aria2.GetPeers"
    GetServers = "aria2.GetServers"
    TellActive = "aria2.tellActive"
    TellWaiting = "aria2.tellWaiting"
    TellStopped = "aria2.tellStopped"
    ChangePosition = "aria2.changePosition"
    ChangeUri = "aria2.changeUri"
    GetOption = "aria2.getOption"
    ChangeOption = "aria2.changeOption"
    GetGlobalOption = "aria2.getGlobalOption"
    ChangeGlobalOption = "aria2.changeGlobalOption"
    GetGlobalStat = "aria2.getGlobalStat"
    PurgeDownloadResult = "aria2.purgeDownloadResult"
    RemoveDownloadResult = "aria2.removeDownloadResult"
    GetVersion = "aria2.getVersion"
    GetSessionInfo = "aria2.getSessionInfo"
    Shutdown = "aria2.shutdown"
    ForceShutdown = "aria2.forceShutdown"
    SaveSession = "aria2.saveSession"
    MultiCall = "system.multicall"


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
    def __init__(self, adapterConfig = None, parent = None):
        super().__init__(parent)
        self._adapterConfig = adapterConfig
        self._ws = None

        self._ids = {}
        self._loop = None
        self._loop_executor = None
        self._loop_thread = threading.Thread(daemon = True,
                                             target = self._startEventLoop,
                                             name = adapterConfig.name)
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

            while True:
                if not self._ready():
                    break

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
    def _cb_tellStopped(self, result):
        print("_cb_tellStopped", result)

    @asyncio.coroutine
    def _cb_onDownloadComplete(self, result):
        print("_cb_onDownloadComplete", result)


class FakeAdapterConfig(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "adapter-Aria2Test"


if __name__ == "__main__":
    config = FakeAdapterConfig(
        connection = "ws://127.0.0.1:6800/jsonrpc",
    )
    adapter = Aria2Adapter(config)
    import time
    time.sleep(1)
    adapter.do_createTask("http://www.baidu.com/robots.txt")
    while True:
        time.sleep(1)
