# -*- coding: utf-8 -*-

import logging
from launcher import app
import asyncio, os, sys
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import threading
from urllib import parse

from PyQt5.QtCore import QObject, pyqtSignal, pyqtProperty
import constants
from Tasks.action import TaskCreation, TaskCreationType
from models.KlassMap import KlassMap
from utils.misc import tryRemove, trySymlink, tryMkdir
from utils.system import getInitType, InitType
from .vanilla import TaskClass, XwareClient, Settings
from .map import TaskMap
from .daemon import callXwared

_POLLING_INTERVAL = 1


class XwareSettings(QObject):
    updated = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self.initialized = False
        self._settings = None

    @pyqtProperty(int, notify = updated)
    def downloadSpeedLimit(self):
        return self._settings.get("downloadSpeedLimit")

    @pyqtProperty(int, notify = updated)
    def uploadSpeedLimit(self):
        return self._settings.get("uploadSpeedLimit")

    @pyqtProperty(int, notify = updated)
    def slStartTime(self):
        return self._settings.get("slStartTime")

    @pyqtProperty(int, notify = updated)
    def slEndTime(self):
        return self._settings.get("slEndTime")

    @pyqtProperty(int, notify = updated)
    def maxRunTaskNumber(self):
        return self._settings.get("maxRunTaskNumber")

    @pyqtProperty(int, notify = updated)
    def autoOpenLixian(self):
        return self._settings.get("autoOpenLixian")

    @pyqtProperty(int, notify = updated)
    def autoOpenVip(self):
        return self._settings.get("autoOpenVip")

    @pyqtProperty(int, notify = updated)
    def autoDlSubtitle(self):
        return self._settings.get("autoDlSubtitle")

    def update(self, settings: Settings):
        self._settings = settings
        self.initialized = True
        self.updated.emit()


class XwareAdapter(QObject):
    initialized = pyqtSignal()
    infoUpdated = pyqtSignal()  # daemon infoPolled

    Manifest = {
        "SupportedTypes": [
            TaskCreationType.Normal, TaskCreationType.Emule, TaskCreationType.Magnet,
            TaskCreationType.RemoteTorrent, TaskCreationType.LocalTorrent,
        ],
    }

    def __init__(self, *, adapterConfig, taskModel, parent = None):
        super().__init__(parent)
        # Prepare XwareClient Variables
        self._ulSpeed = 0
        self._dlSpeed = 0
        self._runningTaskCount = 0
        from .vanilla import GetSysInfo
        self._sysInfo = GetSysInfo(Return = 0, Network = 0, License = 0, Bound = 0,
                                   ActivateCode = "", Mount = 0, InternalVersion = "",
                                   Nickname = "", Unknown = "", UserId = 0, VipLevel = 0)
        self._xwareSettings = XwareSettings(self)

        # Prepare XwaredClient Variables
        self._xwaredRunning = False
        self._etmPid = 0
        self._peerId = ""
        self._startEtmWhen = 1

        self._adapterConfig = adapterConfig
        connection = parse.urlparse(self._adapterConfig["connection"], scheme = "file")
        self.xwaredSocket = None
        self.mountsFaker = None

        self.klassMap = KlassMap(adapter = self, namespace = self.namespace, taskModel = taskModel)
        self.klassMap.addTaskMap(
            TaskMap(klass = TaskClass.RUNNING)
        )
        self.klassMap.addTaskMap(
            TaskMap(klass = TaskClass.COMPLETED)
        )
        self.klassMap.addTaskMap(
            TaskMap(klass = TaskClass.RECYCLED)
        )
        self.klassMap.addTaskMap(
            TaskMap(klass = TaskClass.FAILED_ON_SUBMISSION)
        )

        self.useXwared = False
        self.isLocal = False
        _clientInitOptions = dict()
        if connection.scheme == "file":
            _clientInitOptions["host"] = "127.0.0.1"
            self.useXwared = True
            self.xwaredSocket = os.path.expanduser(connection.path)
            app.aboutToQuit.connect(lambda: self.do_daemon_quitFrontend())
            self._notifyFrontendStart = True
            from .mounts import MountsFaker
            self.mountsFaker = MountsFaker(constants.MOUNTS_FILE)
        elif connection.scheme == "http":
            # assume etm is always running
            self._etmPid = 0xDEADBEEF
            host, port = connection.netloc.split(":")
            self._peerId = connection.query
            _clientInitOptions["host"] = host
            _clientInitOptions["port"] = port
        else:
            raise NotImplementedError()

        self._loop = None
        self._loop_executor = None
        self._xwareClient = None
        self._loop_thread = threading.Thread(daemon = True,
                                             target = self._startEventLoop,
                                             args = (_clientInitOptions,),
                                             name = adapterConfig.name)

    def start(self):
        self._loop_thread.start()

    def _startEventLoop(self, clientInitOptions = None):
        self._loop = asyncio.new_event_loop()
        self._loop.set_debug(True)
        self._loop_executor = ThreadPoolExecutor(max_workers = 1)
        self._loop.set_default_executor(self._loop_executor)
        asyncio.events.set_event_loop(self._loop)
        self._xwareClient = XwareClient()
        self.setClientOptions(clientInitOptions or dict())
        asyncio.async(self.main())
        self._loop.run_forever()

    @pyqtProperty(str, notify = initialized)
    def namespace(self):
        return "xware-" + self._adapterConfig.name[len("adapter-"):]

    @pyqtProperty(str, notify = initialized)
    def name(self):
        return self._adapterConfig["name"]

    @pyqtProperty(str, notify = initialized)
    def connection(self):
        return self._adapterConfig["connection"]

    @property
    def ulSpeed(self):
        return self._ulSpeed

    @property
    def dlSpeed(self):
        return self._dlSpeed

    @property
    def runningTaskCount(self):
        return self._runningTaskCount

    @property
    def backendSettings(self):
        return self._xwareSettings

    def setClientOptions(self, clientOptions: dict):
        host = clientOptions.get("host", None)
        if host in ("127.0.0.1", "localhost"):
            self.isLocal = True

        self._xwareClient.updateOptions(clientOptions)

    # =========================== PUBLIC ===========================
    @asyncio.coroutine
    def main(self):
        # Entry point of the thread "XwareAdapterEventLoop"
        # main() handles non-stop polling
        if getattr(self, "_notifyFrontendStart", False):
            self._loop.call_soon(self.daemon_start)

        while True:
            self._loop.call_soon(self.get_getsysinfo)
            self._loop.call_soon(self.get_list, TaskClass.RUNNING)
            self._loop.call_soon(self.get_list, TaskClass.COMPLETED)
            self._loop.call_soon(self.get_list, TaskClass.RECYCLED)
            self._loop.call_soon(self.get_list, TaskClass.FAILED_ON_SUBMISSION)
            if not self._xwareSettings.initialized:
                self._loop.call_soon(self.get_settings)
            if self.useXwared:
                self._loop.call_soon(self.daemon_infoPoll)
            yield from asyncio.sleep(_POLLING_INTERVAL)

    # =========================== META-PROGRAMMING MAGICS ===========================
    def __getattr__(self, name):
        if name.startswith("get_") or name.startswith("post_"):
            def method(*args):
                clientMethod = getattr(self._xwareClient, name)
                coro = clientMethod(*args)
                assert asyncio.iscoroutine(coro)
                future =asyncio.async(coro)
                cb = getattr(self, "_donecb_" + name, None)
                if cb:
                    cb = partial(cb, *args)
                    future.add_done_callback(cb)
            setattr(self, name, method)
            return method
        elif name.startswith("daemon_"):
            def method(*args):
                assert self.useXwared
                curried = partial(callXwared, self)
                clientMethodName = name[len("daemon_"):]
                asyncio.async(curried(clientMethodName, args))
            setattr(self, name, method)
            return method
        raise AttributeError("XwareAdapter doesn't have a {name}.".format(**locals()))

    @property
    def sysInfo(self):
        return self._sysInfo

    def _donecb_get_getsysinfo(self, future):
        exception = future.exception()
        if not exception:
            result = future.result()
            self._sysInfo = result
        else:
            logging.error("get_getsysinfo failed.")

    def _donecb_get_list(self, klass, future):
        exception = future.exception()
        if not exception:
            result = future.result()

            if klass == TaskClass.RUNNING:
                self._ulSpeed = result["upSpeed"]
                self._dlSpeed = result["dlSpeed"]
                self._runningTaskCount = result["dlNum"]
            self.klassMap.klass(klass).updateData(result["tasks"])
        else:
            logging.error("get_list failed.")

    def _donecb_get_settings(self, future):
        exception = future.exception()
        if not exception:
            result = future.result()
            self._xwareSettings.update(result)
        else:
            logging.error("get/post settings failed.")

    def _donecb_post_settings(self, _: "new settings", future):
        return self._donecb_get_settings(future)

    def do_pauseTasks(self, tasks, options):
        taskIds = map(lambda t: t.realid, tasks)
        self._loop.call_soon_threadsafe(self.post_pause, taskIds)

    def do_startTasks(self, tasks, options):
        taskIds = map(lambda t: t.realid, tasks)
        self._loop.call_soon_threadsafe(self.post_start, taskIds)

    def do_createTask(self, creation: TaskCreation) -> (bool, str):
        if creation.kind not in self.__class__.Manifest["SupportedTypes"]:
            return False, "Not a supported type."

        # convert path
        path = self.mountsFaker.convertToMappedPath(creation.path)
        if not path:
            return False, "Not pre-mounted."

        if creation.kind in (TaskCreationType.Normal, TaskCreationType.Emule) or \
           creation.kind == TaskCreationType.RemoteTorrent:  # TODO xware not properly support yet
            fileInfo = creation.subtaskInfo[0]

            # Workaround: xware doesn't acquire filename if not set.
            filename = fileInfo.name

            self._loop.call_soon_threadsafe(self.post_createTask,
                                            path,
                                            creation.url,
                                            filename)
            return True, None

        elif creation.kind == TaskCreationType.Magnet:
            # Note:
            # To add a magnet task, xware requires a name field, same as normal and emule tasks.
            # But xware will ignore the name parameter and acquire the name on its own.
            self._loop.call_soon_threadsafe(self.post_createTask,
                                            path,
                                            creation.url,
                                            "解析中的磁力链接")
            return True, None
        elif creation.kind == TaskCreationType.LocalTorrent:
            self._loop.call_soon_threadsafe(self.post_createBtTask,
                                            )
        return False, "Not implemented."

    def do_delTasks(self, tasks, options):
        taskIds = map(lambda t: t.realid, tasks)
        self._loop.call_soon_threadsafe(self.post_del,
                                        taskIds,
                                        options["recycle"],
                                        options["delete"])

    def do_restoreTasks(self, tasks, options):
        taskIds = map(lambda t: t.realid, tasks)
        self._loop.call_soon_threadsafe(self.post_restore,
                                        taskIds)

    def do_openLixianChannel(self, taskItem, enable: bool):
        taskId = taskItem.realid
        self._loop.call_soon_threadsafe(self.post_openLixianChannel, taskId, enable)

    def do_openVipChannel(self, taskItem):
        taskId = taskItem.realid
        self._loop.call_soon_threadsafe(self.post_openVipChannel, taskId)

    def do_applySettings(self, settings: dict):
        dLimit = settings.get("downloadSpeedLimit", -1)
        uLimit = settings.get("uploadSpeedLimit", -1)

        if dLimit != -1:
            self._adapterConfig.setint("dlspeedlimit", dLimit)
        if uLimit != -1:
            self._adapterConfig.setint("ulspeedlimit", uLimit)

        self._loop.call_soon_threadsafe(self.post_settings, settings)

    # ==================== DAEMON ====================
    @pyqtProperty(bool, notify = infoUpdated)
    def xwaredRunning(self):
        return self._xwaredRunning

    @pyqtProperty(int, notify = infoUpdated)
    def etmPid(self):
        return self._etmPid

    @pyqtProperty(str, notify = infoUpdated)
    def peerId(self):
        return self._peerId

    @pyqtProperty(int, notify = infoUpdated)
    def startEtmWhen(self):
        return self._startEtmWhen

    @startEtmWhen.setter
    def startEtmWhen(self, value):
        self._loop.call_soon_threadsafe(self.daemon_setStartEtmWhen, value)

    def _donecb_daemon_infoPoll(self, data):
        error = data.get("error")
        if not error:
            result = data.get("result")
            self._xwaredRunning = True
            self._etmPid = result.get("etmPid")
            self._peerId = result.get("peerId")
            lcPort = result.get("lcPort")
            self._startEtmWhen = result.get("startEtmWhen")
        else:
            self._xwaredRunning = False
            self._etmPid = 0
            self._peerId = ""
            lcPort = 0
            self._startEtmWhen = 1
            print("infoPoll failed with error", error, file = sys.stderr)
        self.setClientOptions({
            "port": lcPort,
        })
        self.infoUpdated.emit()

    def do_daemon_start(self):
        self._loop.call_soon_threadsafe(self.daemon_startETM)

    def do_daemon_restart(self):
        self._loop.call_soon_threadsafe(self.daemon_restartETM)

    def do_daemon_stop(self):
        self._loop.call_soon_threadsafe(self.daemon_stopETM)

    def do_daemon_startFrontend(self):
        raise NotImplementedError()
        # handled in main()
        # self._loop.call_soon_threadsafe(self.daemon_start)

    def do_daemon_quitFrontend(self):
        self._loop.call_soon_threadsafe(self.daemon_quit)

    @property
    def daemonManagedBySystemd(self):
        return os.path.lexists(constants.SYSTEMD_SERVICE_ENABLED_USERFILE) and \
            os.path.lexists(constants.SYSTEMD_SERVICE_USERFILE)

    @daemonManagedBySystemd.setter
    def daemonManagedBySystemd(self, on):
        if on:
            tryMkdir(os.path.dirname(constants.SYSTEMD_SERVICE_ENABLED_USERFILE))

            trySymlink(constants.SYSTEMD_SERVICE_FILE,
                       constants.SYSTEMD_SERVICE_USERFILE)

            trySymlink(constants.SYSTEMD_SERVICE_USERFILE,
                       constants.SYSTEMD_SERVICE_ENABLED_USERFILE)
        else:
            tryRemove(constants.SYSTEMD_SERVICE_ENABLED_USERFILE)
            tryRemove(constants.SYSTEMD_SERVICE_USERFILE)
        if getInitType() == InitType.SYSTEMD:
            os.system("systemctl --user daemon-reload")

    @property
    def daemonManagedByUpstart(self):
        return os.path.lexists(constants.UPSTART_SERVICE_USERFILE)

    @daemonManagedByUpstart.setter
    def daemonManagedByUpstart(self, on):
        if on:
            tryMkdir(os.path.dirname(constants.UPSTART_SERVICE_USERFILE))

            trySymlink(constants.UPSTART_SERVICE_FILE,
                       constants.UPSTART_SERVICE_USERFILE)
        else:
            tryRemove(constants.UPSTART_SERVICE_USERFILE)
        if getInitType() == InitType.UPSTART:
            os.system("initctl --user reload-configuration")

    @property
    def daemonManagedByAutostart(self):
        return os.path.lexists(constants.AUTOSTART_DESKTOP_USERFILE)

    @daemonManagedByAutostart.setter
    def daemonManagedByAutostart(self, on):
        if on:
            tryMkdir(os.path.dirname(constants.AUTOSTART_DESKTOP_USERFILE))

            trySymlink(constants.AUTOSTART_DESKTOP_FILE,
                       constants.AUTOSTART_DESKTOP_USERFILE)
        else:
            tryRemove(constants.AUTOSTART_DESKTOP_USERFILE)
