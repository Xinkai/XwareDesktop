# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QMenu, QSystemTrayIcon
from PyQt5.QtGui import QIcon, QPixmap

class Ui_SystemTray(object):
    def setupSystray(self):
        self.trayIconMenu = QMenu(self)

        self.trayIconMenu.addSeparator()

        icon = QIcon()
        icon.addPixmap(QPixmap(":/image/thunder.ico"), QIcon.Normal, QIcon.Off)
        self.trayIconMenu.addAction(self.action_exit)

        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setIcon(icon)
        self.trayIcon.setContextMenu(self.trayIconMenu)
        self.trayIcon.setVisible(True)

        self.trayIcon.activated.connect(self.slotActivateSystrayContextMenu)

    def slotActivateSystrayContextMenu(self, reason):
        if reason == QSystemTrayIcon.Context: # right
            pass
        elif reason == QSystemTrayIcon.MiddleClick: # middle
            pass
        elif reason == QSystemTrayIcon.DoubleClick: # double click
            pass
        elif reason == QSystemTrayIcon.Trigger: # left
            pass


        print("reason: ", reason)