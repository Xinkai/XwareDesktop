# -*- coding: utf-8 -*-

import logging

from PyQt5.QtCore import pyqtSlot, QEvent, Qt
from PyQt5.QtWidgets import QMainWindow

from ui_main import Ui_MainWindow
from PersistentGeometry import PersistentGeometry

class MainWindow(QMainWindow, Ui_MainWindow, PersistentGeometry):
    app = None

    def __init__(self, app):
        super().__init__()
        self.app = app

        # UI
        self.setupUi(self)
        self.connectUI()
        self.preserveGeometry("main")

    def connectUI(self):
        # connect UI related signal/slot
        self.action_exit.triggered.connect(self.slotExit)
        self.action_setting.triggered.connect(self.slotSetting)
        self.action_showAbout.triggered.connect(self.slotShowAbout)

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
        self.app.quit()

    @pyqtSlot()
    def slotSetting(self):
        from settings import SettingsDialog
        self.settingsDialog = SettingsDialog(self)
        self.settingsDialog.show()

    @pyqtSlot()
    def slotShowAbout(self):
        from about import AboutDialog
        self.aboutDialog = AboutDialog(self)
        self.aboutDialog.show()

    def changeEvent(self, qEvent):
        if qEvent.type() == QEvent.WindowStateChange:
            if self.isMinimized():
                if self.app.settings.getbool("frontend", "minimizetosystray"):
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
        if self.app.settings.getbool("frontend", "closetominimize"):
            qCloseEvent.ignore()
            self.minimize()
        else:
            qCloseEvent.accept()
