#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtCore import QUrl, pyqtSlot
from PyQt5.QtWidgets import QApplication, QMainWindow
from ui_main import Ui_MainWindow
from systemtray import Ui_SystemTray
from xwarepy import XwarePy
import constants
log = print

class MainWindow(QMainWindow, Ui_MainWindow, Ui_SystemTray):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setupSystray()

        # hold a reference to setting
        self.setting = settingsAccessor

        # setup Webkit Bridge
        self.xdpy = XwarePy(self)
        self.setupWebkit()
        self.connectUI()
        self.connectXwarePy()


    # initialization
    def setupWebkit(self):
        from PyQt5.QtWebKit import QWebSettings
        self.webView.settings().setAttribute(QWebSettings.DeveloperExtrasEnabled, True)
        self.webView.loadFinished.connect(self.injectXwareJS)
        self.frame.javaScriptWindowObjectCleared.connect(self.slotAddJSObject)
        self.webView.urlChanged.connect(self.slotUrlChanged)

    def connectUI(self):
        # connect UI related signal/slot
        self.action_exit.triggered.connect(self.slotExit)
        self.action_setting.triggered.connect(self.slotSetting)
        self.action_refreshPage.triggered.connect(self.slotRefreshPage)

    def connectXwarePy(self):
        self.action_createTask.triggered.connect(self.slotPrepareTaskCreation)
    # initialization ends

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
        return self.qurl.url()
    # shorthand ends

    def slotAddJSObject(self):
        self.frame.addToJavaScriptWindowObject("xdpy", self.xdpy)

    @pyqtSlot()
    @pyqtSlot(str)
    def slotPrepareTaskCreation(self, task = None):
        if task is None:
            self.xdpy.sigCreateTasks.emit([""])

    def slotUrlChanged(self):
        log("webView urlChanged:", self.url)
        if self.url == constants.LOGIN_PAGE:
            log("url to login page.")

        elif self.url == "http://yuancheng.xunlei.com/":
            log("webView: redirect to V3.")
            self.webView.stop()
            self.webView.load(QUrl("http://yuancheng.xunlei.com/3"))
        elif self.url == "http://yuancheng.xunlei.com/3/":
            pass
        else:
            log("Unable to handle this URL", self.url)

    def slotRefreshPage(self):
        self.webView.load(QUrl("http://yuancheng.xunlei.com/3"))

    @pyqtSlot()
    def slotExit(self):
        app.quit()

    @pyqtSlot()
    def injectXwareJS(self):
        with open("xwarejs.js") as file:
            js = file.read()

        self.frame.evaluateJavaScript(js)

    def slotPageLoadFinished(self):
        print("slotPageLoadFinished!")

        self.login()

    def login(self):
        with open("login.js") as file:
            js = file.read().replace("{username}", settingsAccessor.get("account", "username")) \
                            .replace("{password}", settingsAccessor.get("account", "password"))
        # print(js)
        self.webView.page().mainFrame().evaluateJavaScript(js)

    def slotSetting(self):
        from settings import SettingsDialog
        settingsDialog = SettingsDialog()
        settingsDialog.exec()

    def _printDomainCookies(self):
        from PyQt5.QtCore import QUrl
        cookieJar = self.webView.page().networkAccessManager().cookieJar()
        for cookie in cookieJar.cookiesForUrl(QUrl("http://yuancheng.xunlei.com/")):
            print(bytes(cookie.name()).decode('utf-8'), bytes(cookie.value()).decode('utf-8'))

if __name__ == "__main__":
    import os
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    import settings
    settingsAccessor = settings.settingsAccessor = settings.SettingAccessor()


    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()


    sys.exit(app.exec())


