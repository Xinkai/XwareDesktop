# -*- coding: utf-8 -*-

import logging
from launcher import app

from PyQt5.QtCore import pyqtSlot, QEvent, Qt
from PyQt5.QtWidgets import QMainWindow

from PersistentGeometry import PersistentGeometry

from .about import AboutDialog
from .settings import SettingsDialog
from .ui_main import Ui_MainWindow


class MainWindow(QMainWindow, Ui_MainWindow, PersistentGeometry):
    def __init__(self, parent):
        super().__init__(parent)
        self.settingsDialog = None
        self.aboutDialog = None

        # UI
        self.setupUi(self)
        self.connectUI()
        self.preserveGeometry()

    def connectUI(self):
        # connect UI related signal/slot
        self.action_exit.triggered.connect(self.slotExit)
        self.action_setting.triggered.connect(self.slotSetting)
        self.action_showAbout.triggered.connect(self.slotShowAbout)

        adapter = app.adapterManager[0]
        if adapter.useXwared:
            self.action_ETMstart.triggered.connect(adapter.do_daemon_start)
            self.action_ETMstop.triggered.connect(adapter.do_daemon_stop)
            self.action_ETMrestart.triggered.connect(adapter.do_daemon_restart)
            self.menu_backend.setEnabled(True)

        app.systray.toggleMinimized.connect(self.toggleMinimized)

    # shorthand
    @property
    def page(self):
        return self.webView.page()

    @property
    def frame(self):
        return self.webView.page().mainFrame()
    # shorthand ends

    @pyqtSlot()
    def slotExit(self):
        app.quit()

    @pyqtSlot()
    def slotSetting(self):
        self.settingsDialog = SettingsDialog(self)
        self.settingsDialog.show()

    @pyqtSlot()
    def slotShowAbout(self):
        self.aboutDialog = AboutDialog(self)
        self.aboutDialog.show()

    def changeEvent(self, qEvent):
        if qEvent.type() == QEvent.WindowStateChange:
            if self.isMinimized():
                if app.settings.getbool("frontend", "minimizetosystray"):
                    self.setHidden(True)
        super().changeEvent(qEvent)

    def minimize(self):
        self.showMinimized()

    def restore(self):
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
        if self.isHidden():
            self.setHidden(False)
        self.raise_()

    def closeEvent(self, qCloseEvent):
        if app.settings.getbool("frontend", "closetominimize"):
            qCloseEvent.ignore()
            self.minimize()
        else:
            qCloseEvent.accept()

    @pyqtSlot()
    def toggleMinimized(self):
        if self.isHidden() or self.isMinimized():
            self.restore()
        else:
            self.minimize()
