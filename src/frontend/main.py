# -*- coding: utf-8 -*-

import logging

from PyQt5.QtCore import QUrl, pyqtSlot, QEvent, Qt
from PyQt5.QtWidgets import QMainWindow

import constants
from ui_main import Ui_MainWindow
from PersistentGeometry import PersistentGeometry

log = print

class MainWindow(QMainWindow, Ui_MainWindow, PersistentGeometry):
    app = None

    def __init__(self, app):
        super().__init__()
        self.app = app

        # UI
        self.setupUi(self)
        self.connectUI()

        self.setupWebkit()

        self.preserveGeometry("main")

    def setupWebkit(self):
        self.settings.applySettings.connect(self.applySettingsToWebView)

        self.frame.loadStarted.connect(self.slotFrameLoadStarted)
        self.frame.urlChanged.connect(self.slotUrlChanged)
        self.frame.loadFinished.connect(self.injectXwareDesktop)
        self.webView.load(QUrl(constants.LOGIN_PAGE))

    @pyqtSlot()
    def applySettingsToWebView(self):
        from PyQt5.QtWebKit import QWebSettings

        isDevToolsAllowed = self.settings.getbool("frontend", "enabledeveloperstools")
        self.webView.settings().setAttribute(QWebSettings.DeveloperExtrasEnabled, isDevToolsAllowed)
        if isDevToolsAllowed:
            self.webView.setContextMenuPolicy(Qt.DefaultContextMenu)
        else:
            self.webView.setContextMenuPolicy(Qt.NoContextMenu)

        pluginsAllowed = self.settings.getbool("frontend", "allowflash")
        self.webView.settings().setAttribute(QWebSettings.PluginsEnabled, pluginsAllowed)
        self.frontendpy.sigToggleFlashAvailability.emit(pluginsAllowed)

    def connectUI(self):
        # connect UI related signal/slot
        self.action_exit.triggered.connect(self.slotExit)
        self.action_setting.triggered.connect(self.slotSetting)

        self.action_createTask.triggered.connect(self.app.frontendpy.queue.createTasksAction)
        self.action_refreshPage.triggered.connect(self.slotRefreshPage)

        # Note: The menu actions enable/disable toggling are handled by statusbar.
        self.action_ETMstart.triggered.connect(self.app.xwaredpy.slotStartETM)
        self.action_ETMstop.triggered.connect(self.app.xwaredpy.slotStopETM)
        self.action_ETMrestart.triggered.connect(self.app.xwaredpy.slotRestartETM)

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
    def slotUrlChanged(self):
        if self.page.urlMatch(constants.V2_PAGE):
            log("webView: redirect to V3.")
            self.webView.stop()
            self.frame.load(QUrl(constants.V3_PAGE))
        elif self.page.urlMatchIn(constants.V3_PAGE, constants.LOGIN_PAGE):
            pass
        else:
            log("Unable to handle this URL", self.webView.url().toString())

    @pyqtSlot()
    def slotRefreshPage(self):
        self.frame.load(QUrl(constants.V3_PAGE))

    @pyqtSlot()
    def slotExit(self):
        self.app.quit()

    @pyqtSlot()
    def slotFrameLoadStarted(self):
        self.page.overrideFile = None
        self.app.frontendpy.isPageMaskOn = None
        self.app.frontendpy.isPageOnline = None
        self.app.frontendpy.isPageLogined = None
        self.app.frontendpy.isXdjsLoaded = None

    @pyqtSlot()
    def injectXwareDesktop(self):
        # inject xdpy object
        self.frame.addToJavaScriptWindowObject("xdpy", self.app.frontendpy)

        # inject xdjs script
        with open("xwarejs.js") as file:
            js = file.read()
        self.frame.evaluateJavaScript(js)

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
