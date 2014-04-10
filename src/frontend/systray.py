# -*- coding: utf-8 -*-

import logging

from PyQt5.QtCore import pyqtSlot, QObject
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu

from Compat.CompatSystemTrayIcon import CompatSystemTrayIcon


class Systray(QObject):
    app = None
    trayIconMenu = None

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.mainWin = self.app.mainWin

        self.trayIconMenu = QMenu(None)

        icon = QIcon(":/image/thunder.ico")

        self.trayIcon = CompatSystemTrayIcon(self)
        self.trayIcon.setIcon(icon)
        self.trayIcon.setContextMenu(self.trayIconMenu)
        self.trayIcon.setVisible(True)

        self.trayIcon.activated.connect(self.slotSystrayActivated)
        self.trayIconMenu.addAction(self.mainWin.action_exit)

    @pyqtSlot(QSystemTrayIcon.ActivationReason)
    def slotSystrayActivated(self, reason):
        if reason == QSystemTrayIcon.Context:  # right
            pass
        elif reason == QSystemTrayIcon.MiddleClick:  # middle
            pass
        elif reason == QSystemTrayIcon.DoubleClick:  # double click
            pass
        elif reason == QSystemTrayIcon.Trigger:  # left
            if self.mainWin.isHidden() or self.mainWin.isMinimized():
                self.mainWin.restore()
            else:
                self.mainWin.minimize()
