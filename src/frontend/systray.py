# -*- coding: utf-8 -*-

import logging

from PyQt5.QtCore import pyqtSlot, QObject
from PyQt5.QtGui import QIcon
from PyQt5.Qt import Qt
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu

class Systray(QObject):
    app = None
    trayIconMenu = None

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.mainWin = self.app.mainWin

        self.trayIconMenu = QMenu(None)

        icon = QIcon(":/image/thunder.ico")

        self.trayIcon = QSystemTrayIcon(None)
        self.trayIcon.setIcon(icon)
        self.trayIcon.setContextMenu(self.trayIconMenu)
        self.trayIcon.setVisible(True)

        self.trayIcon.activated.connect(self.slotSystrayActivated)
        self.app.lastWindowClosed.connect(self.slotTeardown)

        if self.mainWin:
            self.trayIconMenu.addAction(self.mainWin.action_exit)

    @pyqtSlot()
    def slotTeardown(self):
        print("teardown Systray")
        # On Ubuntu 13.10, systrayicon won't destroy itself gracefully, stops the whole program from exiting.
        del self.trayIcon

    @pyqtSlot(QSystemTrayIcon.ActivationReason)
    def slotSystrayActivated(self, reason):
        if not self.mainWin:
            return

        if reason == QSystemTrayIcon.Context: # right
            pass
        elif reason == QSystemTrayIcon.MiddleClick: # middle
            pass
        elif reason == QSystemTrayIcon.DoubleClick: # double click
            pass
        elif reason == QSystemTrayIcon.Trigger: # left
            if self.app.settings.getbool("frontend", "minimizetosystray"):
                if self.mainWin.isHidden():
                    self.mainWin.setVisible(True)
                    self.mainWin.setWindowState(self.mainWin.savedWindowState)
                else:
                    self.mainWin.setWindowState(Qt.WindowMinimized)
            else:
                if self.mainWin.isMinimized():
                    self.mainWin.setWindowState(self.mainWin.savedWindowState)
                else:
                    self.mainWin.setWindowState(Qt.WindowMinimized)
