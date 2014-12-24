# -*- coding: utf-8 -*-

from launcher import app
from PyQt5.QtCore import QObject, pyqtSignal, pyqtProperty, pyqtSlot, QTimer

from collections import OrderedDict


class AdapterManager(QObject):
    summaryUpdated = pyqtSignal()

    def __init__(self, parent = None):
        super().__init__(parent)
        self._adapters = OrderedDict()
        self._timer = QTimer(self)
        self._timer.timeout.connect(lambda: self.summaryUpdated.emit())
        self._timer.start(1000)

    @pyqtProperty(int, notify = summaryUpdated)
    def ulSpeed(self):
        return sum(map(lambda a: a.ulSpeed, self._adapters.values()))

    @pyqtProperty(int, notify = summaryUpdated)
    def dlSpeed(self):
        return sum(map(lambda a: a.dlSpeed, self._adapters.values()))

    @pyqtProperty(int, notify = summaryUpdated)
    def runningTaskCount(self):
        return sum(map(lambda a: a.runningTaskCount, self._adapters.values()))

    def _registerAdapter(self, adapter):
        ns = adapter.namespace
        assert ns not in self._adapters
        self._adapters[ns] = adapter
        app.taskModel.adapterMap.addKlassMap(adapter.klassMap)

    @pyqtSlot(str, result = "QVariant")
    def adapter(self, ns):
        return self._adapters[ns]

    @pyqtSlot(result = "QStringList")
    def itr(self):
        return self._adapters.keys()

    def __getitem__(self, item):
        assert item == 0
        return self._adapters["xware-legacy"]

    def loadAdapter(self, adapterConfig):
        if adapterConfig["type"] == "xware":
            from libxware import XwareAdapter
            adapter = XwareAdapter(
                adapterConfig = adapterConfig,
                parent = self,
                taskModel = app.taskModel
            )
            self._registerAdapter(adapter)
            adapter.start()
        elif adapterConfig["type"] == "aria2":
            from libaria2 import Aria2Adapter
            adapter = Aria2Adapter(
                adapterConfig = adapterConfig,
                parent = self,
                taskModel = app.taskModel
            )
            self._registerAdapter(adapter)
            adapter.start()
        else:
            raise NotImplementedError()
