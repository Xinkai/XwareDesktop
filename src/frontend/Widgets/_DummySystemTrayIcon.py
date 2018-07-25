# -*- coding: utf-8 -*-

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QSystemTrayIcon


class DummySystemTrayIcon(QObject):
    activated = pyqtSignal(QSystemTrayIcon.ActivationReason)

    def setIcon(self, qIcon):
        pass

    def setContextMenu(self, qMenu):
        pass

    def setVisible(self, visible):
        pass
