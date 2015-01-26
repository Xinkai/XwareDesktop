# -*- coding: utf-8 -*-

import logging
from launcher import app

from PyQt5.QtCore import pyqtSlot

from Widgets import CompatSystemTrayIcon, CompatIcon
from PyQt5.QtWidgets import QSystemTrayIcon

from .contextmenu import ContextMenu


class Systray(CompatSystemTrayIcon):
    def __init__(self, parent = None):
        super().__init__(parent)
        icon = CompatIcon.fromTheme("xware-desktop")
        self.setIcon(icon)
        self.trayIconMenu = ContextMenu(None)
        self.setContextMenu(self.trayIconMenu)
        self.setVisible(True)
        self.activated.connect(self.slotActivated)
        app.aboutToQuit.connect(self.teardown)

    @pyqtSlot(QSystemTrayIcon.ActivationReason)
    def slotActivated(self, reason):
        if reason == QSystemTrayIcon.Context:  # right
            pass
        elif reason == QSystemTrayIcon.MiddleClick:  # middle
            pass
        elif reason == QSystemTrayIcon.DoubleClick:  # double click
            pass
        elif reason == QSystemTrayIcon.Trigger:  # left
            app.toggleMinimized.emit()

    @pyqtSlot()
    def teardown(self):
        self.trayIconMenu.deleteLater()
        self.deleteLater()
