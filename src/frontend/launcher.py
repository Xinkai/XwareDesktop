#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtCore import QUrl, pyqtSlot
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel
from ui_main import Ui_MainWindow
from systemtray import Ui_SystemTray
from xwarepy import XwarePy
import threading
import constants
import mounts
log = print

class MainWindow(QMainWindow, Ui_MainWindow, Ui_SystemTray):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setupSystray()


        self.setting = settingsAccessor # hold a reference to setting

        self.xdpy = XwarePy(self) # setup Webkit Bridge
        self.setupWebkit()
        self.connectUI()
        self.connectXwarePy()
        self.setupStatusBarActions()
        self.mountsFaker = mounts.MountsFaker()


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

    def setupStatusBarActions(self):
        ETMstatus = QLabel(self.statusBar)
        ETMstatus.setObjectName("label_ETMstatus")
        ETMstatus.setText("<font color=''></font>")
        self.statusBar.ETMstatus = ETMstatus
        self.statusBar.addPermanentWidget(ETMstatus)

        daemonStatus = QLabel(self.statusBar)
        daemonStatus.setObjectName("label_daemonStatus")
        daemonStatus.setText("<font color=''></font>")
        self.statusBar.daemonStatus = daemonStatus
        self.statusBar.addPermanentWidget(daemonStatus)

        import ipc
        self.action_ETMstart.triggered.connect(lambda: ipc.DaemonCommunication().startETM())
        self.action_ETMstop.triggered.connect(lambda: ipc.DaemonCommunication().stopETM())
        self.action_ETMrestart.triggered.connect(lambda: ipc.DaemonCommunication().restartETM())

        t = threading.Thread(target = self.startStatusBarThread, daemon = True)
        t.start()

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

    def slotSetting(self):
        from settings import SettingsDialog
        settingsDialog = SettingsDialog(self)
        settingsDialog.exec()

    def _printDomainCookies(self):
        from PyQt5.QtCore import QUrl
        cookieJar = self.webView.page().networkAccessManager().cookieJar()
        for cookie in cookieJar.cookiesForUrl(QUrl("http://yuancheng.xunlei.com/")):
            print(bytes(cookie.name()).decode('utf-8'), bytes(cookie.value()).decode('utf-8'))

    def startStatusBarThread(self):
        import time, fcntl
        while True:
            try:
                daemonLockFile = open(constants.DAEMON_LOCK)
                try:
                    daemonLock = fcntl.flock(daemonLockFile, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    daemonStatus = False
                    fcntl.flock(daemonLockFile, fcntl.LOCK_UN)
                except BlockingIOError:
                    daemonStatus = True
                daemonLockFile.close()
            except FileNotFoundError:
                daemonStatus = False
            if daemonStatus:
                self.statusBar.daemonStatus.setText("<font color='green'>Daemon运行中</font>")
            else:
                self.statusBar.daemonStatus.setText("<font color='red'>Daemon未启动</font>")


            try:
                etmLockFile = open(constants.ETM_LOCK)
                try:
                    etmLock = fcntl.flock(etmLockFile, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    etmStatus = False
                    fcntl.flock(etmLockFile, fcntl.LOCK_UN)
                except BlockingIOError:
                    etmStatus = True
                etmLockFile.close()
            except FileNotFoundError:
                etmStatus = False
            if etmStatus:
                self.statusBar.ETMstatus.setText("<font color='green'>ETM运行中</font>")
            else:
                self.statusBar.ETMstatus.setText("<font color='red'>ETM未启动</font>")

            if not daemonStatus:
                self.action_ETMstart.setEnabled(False)
                self.action_ETMstop.setEnabled(False)
                self.action_ETMrestart.setEnabled(False)
            else:
                if etmStatus:
                    self.action_ETMstart.setEnabled(False)
                    self.action_ETMstop.setEnabled(True)
                    self.action_ETMrestart.setEnabled(True)
                else:
                    self.action_ETMstart.setEnabled(True)
                    self.action_ETMstop.setEnabled(False)
                    self.action_ETMrestart.setEnabled(False)

            time.sleep(1)

if __name__ == "__main__":
    import os
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    tasks = sys.argv[1:]
    import fcntl
    fd = os.open(constants.FRONTEND_LOCK, os.O_RDWR | os.O_CREAT, mode = 0o666)

    import ipc
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        if len(tasks) == 0:
            print("You already have an Xware Desktop instance running.")
            exit(-1)
        else:
            print(tasks)
            ipc.FrontendCommunicationClient(tasks)
            exit(0)

    import settings
    settingsAccessor = settings.settingsAccessor = settings.SettingAccessor()


    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    ipcListener = ipc.FrontendCommunicationListener(window)

    sys.exit(app.exec())


