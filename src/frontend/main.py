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

        self.action_createTask.triggered.connect(self.frontendpy.queue.createTasksAction)
        self.action_refreshPage.triggered.connect(self.slotRefreshPage)

        # Note: The menu actions enable/disable toggling are handled by statusbar.
        self.action_ETMstart.triggered.connect(self.xwaredpy.slotStartETM)
        self.action_ETMstop.triggered.connect(self.xwaredpy.slotStopETM)
        self.action_ETMrestart.triggered.connect(self.xwaredpy.slotRestartETM)

        self.action_showAbout.triggered.connect(self.slotShowAbout)

    # shorthand
    @property
    def page(self):
        return self.webView.page()

    @property
    def frame(self):
        return self.webView.page().mainFrame()

    @property
    def qurl(self):
        return self.webView.url()

    @property
    def url(self):
        # for some reason, on Ubuntu QUrl.url() is not there, call toString() instead.
        return self.qurl.toString()

    @property
    def settings(self):
        return self.app.settings

    @property
    def xwaredpy(self):
        return self.app.xwaredpy

    @property
    def etmpy(self):
        return self.app.etmpy

    @property
    def mountsFaker(self):
        return self.app.mountsFaker

    @property
    def frontendpy(self):
        return self.app.frontendpy
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
            log("Unable to handle this URL", self.url)

    @pyqtSlot()
    def slotRefreshPage(self):
        self.frame.load(QUrl(constants.V3_PAGE))

    @pyqtSlot()
    def slotExit(self):
        self.app.quit()

    @pyqtSlot()
    def slotFrameLoadStarted(self):
        self.page.overrideFile = None
        self.frontendpy.isPageMaskOn = None
        self.frontendpy.isPageOnline = None
        self.frontendpy.isPageLogined = None
        self.frontendpy.isXdjsLoaded = None

    @pyqtSlot()
    def injectXwareDesktop(self):
        # inject xdpy object
        self.frame.addToJavaScriptWindowObject("xdpy", self.frontendpy)

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
                if self.settings.getbool("frontend", "minimizetosystray"):
                    self.setHidden(True)
        super().changeEvent(qEvent)

    def minimize(self):
        self.showMinimized()

    def restore(self):
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
        if self.isHidden():
            self.setHidden(False)

    def closeEvent(self, qCloseEvent):
        if self.settings.getbool("frontend", "closetominimize"):
            qCloseEvent.ignore()
            self.minimize()
        else:
            qCloseEvent.accept()
