# -*- coding: utf-8 -*-

import logging

from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import Qt, QObject, pyqtSignal, pyqtSlot, QUrl, QVariant
import collections

import constants, actions
from actions import FrontendActionsQueue

FrontendStatus = collections.namedtuple("FrontendStatus", ["xdjsLoaded", "logined", "online"])

# Together with xwarejs.js, exchange information with the browser
class FrontendPy(QObject):
    sigCreateTasks = pyqtSignal("QStringList")
    sigCreateTaskFromTorrentFile = pyqtSignal()
    sigCreateTaskFromTorrentFileDone = pyqtSignal()
    sigLogin = pyqtSignal(str, str)
    sigToggleFlashAvailability = pyqtSignal(bool)
    sigActivateDevice = pyqtSignal(str)
    sigNotifyPeerId = pyqtSignal(str) # let xdjs knows peerid
    sigFrontendStatusChanged = pyqtSignal() # caused by webpage heartbeat/changed status/refresh page

    app = None
    queue = None
    isPageMaskOn = None
    _isPageOnline = None # property wraps them, in order to fire sigFrontendStatusChanged
    _isPageLogined = None
    _isXdjsLoaded = None

    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.app.settings.applySettings.connect(self.tryLogin)
        self.queue = FrontendActionsQueue(self)

    @property
    def mainWin(self):
        try:
            mainWin = self.app.mainWin
        except AttributeError:
            raise Exception("frontendpy didn't wait for mainWin.")
        return mainWin

    @property
    def isPageOnline(self):
        return self._isPageOnline

    @isPageOnline.setter
    def isPageOnline(self, value):
        self._isPageOnline = value
        self.sigFrontendStatusChanged.emit()

    @property
    def isPageLogined(self):
        return self._isPageLogined

    @isPageLogined.setter
    def isPageLogined(self, value):
        self._isPageLogined = value
        self.sigFrontendStatusChanged.emit()

    @property
    def isXdjsLoaded(self):
        return self._isXdjsLoaded

    @isXdjsLoaded.setter
    def isXdjsLoaded(self, value):
        self._isXdjsLoaded = value
        self.sigFrontendStatusChanged.emit()
    ################################### SLOTS ######################################
    @pyqtSlot()
    def tryLogin(self):
        if self.app.mainWin.page.urlMatch(constants.LOGIN_PAGE):
            autologin = self.app.settings.getbool("account", "autologin")
            if autologin:
                username = self.app.settings.get("account", "username")
                password = self.app.settings.get("account", "password")
                if username and password:
                    self.sigLogin.emit(username, password)

    def tryActivate(self, payload):
        if not self.app.mainWin.page.urlMatch(constants.V3_PAGE):
            return # not v3 page

        if not payload["userid"]:
            return # not logged in

        userid, status, code, peerid = self.app.etmpy.getActivationStatus()

        if userid == 0:
            # unbound
            if status == -1:
                QMessageBox.warning(None, "Xware Desktop 警告", "ETM未启用，无法激活。需要启动ETM后，刷新页面。",
                                    QMessageBox.Ok, QMessageBox.Ok)
                return

            elif status == 0 and code:
                self.sigActivateDevice.emit(code) # to activate
                return

        else:
            if status == 0 and code:
                # re-activate
                self.sigActivateDevice.emit(code)
                return

            elif userid != int(payload["userid"]):
                QMessageBox.warning(None, "Xware Desktop 警告", "登录的迅雷账户不是绑定的迅雷账户。",
                                    QMessageBox.Ok, QMessageBox.Ok)
                return

            elif peerid not in payload["peerids"]:
                logging.warning("Network is slow, there're no peerids when xdjs loaded.")

            self.sigNotifyPeerId.emit(peerid)

    @pyqtSlot(QVariant)
    def xdjsLoaded(self, payload):
        print("xdjs loaded")
        self.isXdjsLoaded = True
        self.tryLogin()
        self.tryActivate(payload)
        self.consumeAction("xdjs loaded")

    @pyqtSlot()
    def requestFocus(self):
        self.mainWin.frame.setFocus()

    @pyqtSlot(str)
    def systemOpen(self, url):
        from PyQt5.QtGui import QDesktopServices
        url = self.app.mountsFaker.convertToNativePath(url)
        qurl = QUrl(url)
        qurl.setScheme("file")
        QDesktopServices().openUrl(qurl)

    @pyqtSlot(str, str)
    def saveCredentials(self, username, password):
        self.app.settings.set("account", "username", username)
        self.app.settings.set("account", "password", password)
        self.app.settings.setbool("account", "autologin", True)
        self.app.settings.save()

    @pyqtSlot("QList<QVariant>")
    def log(self, items):
        print("xdjs: ", end = "")
        for item in items:
            print(item, end = " ")
        print("")

    @pyqtSlot(bool)
    def slotMaskOnOffChanged(self, val):
        self.isPageMaskOn = val
        if not val:
            self.consumeAction("action acted")
        print("Mask on", val)

    @pyqtSlot(bool)
    def slotSetOnline(self, online):
        self.isPageOnline = online

    @pyqtSlot(bool)
    def slotSetLogined(self, logined):
        self.isPageLogined = logined

    @pyqtSlot()
    def consumeAction(self, reason):
        print("Try to consume, because {}.".format(reason))
        if not self.isPageOnline:
            print("Xdjs says device not online, no consuming")
            return

        if self.isPageMaskOn:
            print("Mask on, no consuming")
            return

        if not self.isXdjsLoaded:
            print("Xdjs not ready, no consuming")
            return

        if not self.isPageLogined:
            print("page not logined, no consuming")
            return

        try:
            action = self.queue.dequeueAction()
        except IndexError:
            print("Nothing to consume")
            # no actions
            return

        print("consuming action", action)
        if isinstance(action, actions.CreateTasksAction):
            taskUrls = list(map(lambda task: task.url, action.tasks))
            if action.tasks[0].kind == actions.CreateTask.NORMAL:
                self.sigCreateTasks.emit(taskUrls)
            else:
                self.mainWin.page.overrideFile = taskUrls[0]
                self.sigCreateTaskFromTorrentFile.emit()

    @pyqtSlot()
    def slotClickBtButton(self):
        from PyQt5.QtGui import QKeyEvent
        from PyQt5.QtCore import QEvent
        keydownEvent = QKeyEvent(QEvent.KeyPress, # type
                                 Qt.Key_Enter,    # key
                                 Qt.NoModifier)   # modifiers

        self.app.sendEvent(self.mainWin.webView, keydownEvent)
        self.sigCreateTaskFromTorrentFileDone.emit()

    def getFrontendStatus(self):
        return FrontendStatus(self.isXdjsLoaded, self.isPageLogined, self.isPageOnline)
