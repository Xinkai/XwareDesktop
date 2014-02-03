#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QApplication, QMainWindow
from ui_main import Ui_MainWindow
from systemtray import Ui_SystemTray

log = print

class MainWindow(QMainWindow, Ui_MainWindow, Ui_SystemTray):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setupSystray()

        self.action_exit.triggered.connect(self.slotExit)
        self.action_setting.triggered.connect(self.slotSetting)

        # self.webView.loadFinished.connect(self.slotPageLoadFinished)
        self.action_createTask.triggered.connect(self.slotCreateTask)
        self.action_refreshPage.triggered.connect(self.slotRefreshPage)
        self.webView.urlChanged.connect(self.slotUrlChanged)


    def slotCreateTask(self):
        with open("createTask.js") as file:
            js = file.read().replace("{username}", settingsAccessor.get("account", "username")) \
                            .replace("{password}", settingsAccessor.get("account", "password"))
        self.webView.page().mainFrame().evaluateJavaScript(js)

    def slotUrlChanged(self):
        url = self.webView.url().url()
        log("webView urlChanged:", url)
        if url == "http://yuancheng.xunlei.com/login.html":
            log("login????")
        elif url == "http://yuancheng.xunlei.com/":
            log("webView: redirect to V3.")
            self.webView.stop()
            self.webView.load(QUrl("http://yuancheng.xunlei.com/3"))
        elif url == "http://yuancheng.xunlei.com/3/":
            pass
        else:
            log("Unable to handle this URL", url)

    def slotRefreshPage(self):
        self.webView.load(QUrl("http://yuancheng.xunlei.com/3"))

    def slotExit(self):
        app.quit()

    def slotAddTask(self):
        pass

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
    import settings

    settingsAccessor = settings.settingsAccessor = settings.SettingAccessor()


    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()


    sys.exit(app.exec())


