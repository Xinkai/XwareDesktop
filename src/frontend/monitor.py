# -*- coding: utf-8 -*-

import logging

from PyQt5.QtCore import pyqtSignal
from PyQt5.Qt import Qt
from PyQt5.QtGui import QGuiApplication

import threading, time

from ui_monitor import MonitorWidget, Ui_Form

class MonitorWindow(MonitorWidget, Ui_Form):
    sigTaskUpdating = pyqtSignal(dict)

    app = None
    _stat = None
    _thread = None

    def __init__(self, parent = None):
        super().__init__(parent)
        self.setupUi(self)
        self.setStyleSheet("background-color: rgba(135, 206, 235, 0.8)")
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.app = QGuiApplication.instance()
        self._thread = threading.Thread(target = self.updateSpeedsThread,
                                        name = "monitor speeds updating",
                                        daemon = True)
        self._thread.start()

    def updateSpeedsThread(self):
        while True:
            runningTaskIds = self.app.etmpy.runningTasksStat.getTIDs()
            for tid in runningTaskIds:
                task = self.app.etmpy.runningTasksStat.getTask(tid)
                logging.debug("updateSpeedsThread, deadlock incoming, maybe")
                self.sigTaskUpdating.emit(task)
                time.sleep(1)
                break
            else:
                time.sleep(1)

