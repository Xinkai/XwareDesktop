# -*- coding: utf-8 -*-

from launcher import app
from PyQt5.QtCore import pyqtProperty, pyqtSignal, QObject


class Aria2TaskItem(QObject):
    def __init__(self, *, adapter):
        super().__init__(None)
        self._adapter = adapter

        self.moveToThread(self._adapter.thread())
        self.setParent(self._adapter)
