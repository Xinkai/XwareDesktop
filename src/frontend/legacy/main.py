# -*- coding: utf-8 -*-

import logging

from PyQt5.QtCore import pyqtSlot, QEvent, Qt
from PyQt5.QtWidgets import QMainWindow

from PersistentGeometry import PersistentGeometry

from .about import AboutDialog
from .settings import SettingsDialog
from .ui_main import Ui_MainWindow

class MainWindow(QMainWindow, Ui_MainWindow, PersistentGeometry):
    def __init__(self, *, adapter, taskCreationAgent, frontendSettings, app):
        super().__init__(None)
        self.settingsDialog = None
        self.aboutDialog = None
        self.__adapter = adapter
        self.__taskCreationAgent = taskCreationAgent
        self.__frontendSettings = frontendSettings
        self.__app = app
        # UI
        self.setupUi(self)
        self.connectUI()
        self.preserveGeometry()
        self.__app.aboutToQuit.connect(self.teardown)

    def connectUI(self):
        # connect UI related signal/slot
        self.action_exit.triggered.connect(self.slotExit)
        self.action_setting.triggered.connect(self.slotSetting)
        self.action_showAbout.triggered.connect(self.slotShowAbout)

        if self.__adapter.useXwared:
            self.action_ETMstart.triggered.connect(self.__adapter.do_daemon_start)
            self.action_ETMstop.triggered.connect(self.__adapter.do_daemon_stop)
            self.action_ETMrestart.triggered.connect(self.__adapter.do_daemon_restart)
            self.menu_backend.setEnabled(True)

        self.__app.toggleMinimized.connect(self.toggleMinimized)
        self.action_createTask.triggered.connect(self.__taskCreationAgent.createTasksAction)

    # shorthand
    @property
    def page(self):
        return self.webView.page()

    @pyqtSlot()
    def slotExit(self):
        self.__app.quit()

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
                if self.__frontendSettings.getbool("minimizetosystray"):
                    self.setHidden(True)
        super().changeEvent(qEvent)

    def minimize(self):
        self.showMinimized()

    def restore(self):
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
        if self.isHidden():
            self.setHidden(False)
        self.activateWindow()
        self.raise_()

    def closeEvent(self, qCloseEvent):
        if self.__frontendSettings.getbool("closetominimize"):
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

    @pyqtSlot()
    def teardown(self):
        self.deleteLater()
