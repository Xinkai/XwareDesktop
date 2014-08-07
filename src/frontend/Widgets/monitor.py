# -*- coding: utf-8 -*-

import logging
from launcher import app

from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QPoint, QTimer

from models.TaskModel import TaskClass
from .ui_monitor import MonitorWidget, Ui_MonitorWindow
from PersistentGeometry import PersistentGeometry
from .contextmenu import ContextMenu


class MonitorWindow(MonitorWidget, Ui_MonitorWindow, PersistentGeometry):
    sigTaskUpdating = pyqtSignal("QObject")

    def __init__(self, parent = None):
        super().__init__(parent)
        self.setupUi(self)
        self.setStyleSheet("background-color: rgba(135, 206, 235, 0.8)")
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.TICKS_PER_TASK = 4
        self.TICK_INTERVAL = 1000  # in milliseconds

        app.applySettings.connect(self._setMonitorFullSpeed)
        self._setMonitorFullSpeed()

        self.preserveGeometry()
        self._contextMenu = ContextMenu(None)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.advance)
        self._timer.start(self.TICK_INTERVAL)
        self._taskIterator = self._runningTasksIterator()

    @pyqtSlot()
    def advance(self):
        task = next(self._taskIterator)
        self.sigTaskUpdating.emit(task)

    def _runningTasksIterator(self):
        taskManager = app.taskModel.taskManager
        while True:
            found = False
            for id_, item in taskManager.items():
                if item.klass == TaskClass.RUNNING:
                    for i in range(self.TICKS_PER_TASK):
                        found = True
                        yield item
            if not found:
                yield None

    @pyqtSlot()
    def _setMonitorFullSpeed(self):
        fullSpeed = app.settings.getint("frontend", "monitorfullspeed")
        logging.info("monitor full speed -> {}".format(fullSpeed))
        self.graphicsView.FULLSPEED = 1024 * fullSpeed

    @pyqtSlot(QPoint)
    def showContextMenu(self, qPoint):
        self._contextMenu.exec(self.mapToGlobal(qPoint))
