# -*- coding: utf-8 -*-

import logging
from launcher import app

from PyQt5.QtCore import pyqtSlot, QObject
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QSystemTrayIcon

from .contextmenu import ContextMenu


class Systray(QObject):
    def __init__(self, parent):
        super().__init__(parent)

        self.trayIconMenu = ContextMenu(None)

        icon = QIcon.fromTheme("xware-desktop")

        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setIcon(icon)
        self.trayIcon.setContextMenu(self.trayIconMenu)
        self.trayIcon.setVisible(True)

        self.trayIcon.activated.connect(self.slotSystrayActivated)

    @pyqtSlot(QSystemTrayIcon.ActivationReason)
    def slotSystrayActivated(self, reason):
        if reason == QSystemTrayIcon.Context:  # right
            pass
        elif reason == QSystemTrayIcon.MiddleClick:  # middle
            pass
        elif reason == QSystemTrayIcon.DoubleClick:  # double click
            pass
        elif reason == QSystemTrayIcon.Trigger:  # left
            if app.mainWin.isHidden() or app.mainWin.isMinimized():
                app.mainWin.restore()
            else:
                app.mainWin.minimize()
