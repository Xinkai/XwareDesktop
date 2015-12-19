# -*- coding: utf-8 -*-

import logging

from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import Qt, QObject, pyqtSignal, pyqtSlot, QVariant, QEvent
from PyQt5.QtGui import QKeyEvent

import collections

import constants
from Tasks.action import TaskCreationType
from utils.system import systemOpen, viewOneFile

FrontendStatus = collections.namedtuple("FrontendStatus", ["xdjsLoaded", "logined", "online"])


# Together with xwarejs.js, exchange information with the browser
class FrontendPy(QObject):
    sigCreateTask = pyqtSignal(str)
    sigCreateTaskFromTorrentFile = pyqtSignal()
    sigCreateTaskFromTorrentFileDone = pyqtSignal()
    sigLogin = pyqtSignal(str, str)
    sigToggleFlashAvailability = pyqtSignal(bool)
    sigActivateDevice = pyqtSignal(str)
    sigNotifyPeerId = pyqtSignal(str)  # let xdjs knows peerid
    sigFrontendStatusChanged = pyqtSignal()  # caused by page heartbeat/changed status/refresh page

    def __init__(self, *, taskCreationAgent, legacySettings, adapterSettings, adapter, mainWin,
                 parent):
        super().__init__(parent)
        self.__taskCreationAgent = taskCreationAgent
        self.__legacySettings = legacySettings
        self.__adapterSettings = adapterSettings
        self.__adapter = adapter
        self.__mainWin = mainWin
        self.__app = parent

        self._isPageMaskOn = None
        self._isPageOnline = None  # property wraps them, in order to fire sigFrontendStatusChanged
        self._isPageLogined = None
        self._isXdjsLoaded = None
        self.__taskCreationAgent.available.connect(lambda: self.createTask("available"))
        self.__mainWin.page.sigFrameLoadStarted.connect(self.frameLoadStarted)
        self.sigFrontendStatusChanged.connect(
            self.__mainWin.statusBar_main.slotFrontendStatusChanged)
        self.__app.applySettings.connect(self.tryLogin)

    @property
    def isPageMaskOn(self):
        return self._isPageMaskOn

    @isPageMaskOn.setter
    def isPageMaskOn(self, value):
        self._isPageMaskOn = value
        if self._isPageMaskOn is False:
            self.createTask("mask off")

    @property
    def isPageOnline(self):
        return self._isPageOnline

    @isPageOnline.setter
    def isPageOnline(self, value):
        if self._isPageOnline == value:
            return  # Heartbeat, don't need to continue if online status stays the same
        self._isPageOnline = value
        self.sigFrontendStatusChanged.emit()
        if self._isPageOnline:
            self.createTask("online")

    @property
    def isPageLogined(self):
        return self._isPageLogined

    @isPageLogined.setter
    def isPageLogined(self, value):
        self._isPageLogined = value
        self.sigFrontendStatusChanged.emit()
        if self._isPageLogined:
            self.createTask("logined")

    @property
    def isXdjsLoaded(self):
        return self._isXdjsLoaded

    @isXdjsLoaded.setter
    def isXdjsLoaded(self, value):
        self._isXdjsLoaded = value
        self.sigFrontendStatusChanged.emit()
        if self._isXdjsLoaded:
            self.createTask("xdjs loaded")

    @pyqtSlot()
    def tryLogin(self):
        if self.__mainWin.page.urlMatchIn(constants.LOGIN_PAGE):
            autologin = self.__legacySettings.getbool("autologin")
            print(self.__adapterSettings.addons_loaded, "<-- loaded")
            if autologin:
                username = self.__adapterSettings.myGet("username")
                password = self.__adapterSettings.myGet("password")
                if username and password:
                    self.sigLogin.emit(username, password)

    def tryActivate(self, payload):
        if not self.__mainWin.page.urlMatchIn(constants.V3_PAGE):
            return  # not v3 page

        if not payload["userid"]:
            return  # not logged in

        userid = int(self.__adapter.sysInfo.UserId)
        status = self.__adapter.sysInfo.Bound
        code = self.__adapter.sysInfo.ActivateCode
        peerid = self.__adapter.peerId

        if userid == 0:
            # unbound
            if status == -1:
                QMessageBox.warning(None, "Xware Desktop 警告", "ETM未启用，无法激活。需要启动ETM后，刷新页面。",
                                    QMessageBox.Ok, QMessageBox.Ok)
                return

            elif status == 0 and code:
                self.sigActivateDevice.emit(code)  # to activate
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

    @pyqtSlot()
    def frameLoadStarted(self):
        self.isPageMaskOn = None
        self.isPageOnline = None
        self.isPageLogined = None
        self.isXdjsLoaded = None

    @pyqtSlot(QVariant)
    def xdjsLoaded(self, payload):
        logging.info("xdjs loaded")
        self.isXdjsLoaded = True
        self.tryLogin()
        self.tryActivate(payload)

    @pyqtSlot()
    def requestFocus(self):
        self.__mainWin.restore()
        self.__mainWin.frame.setFocus()

    @pyqtSlot(str)
    def systemOpen(self, url):
        if self.__adapter.mountsFaker:
            systemOpen(self.__adapter.mountsFaker.convertToLocalPath(url))

    @pyqtSlot(str)
    def systemViewOneFile(self, url):
        if self.__adapter.mountsFaker:
            viewOneFile(self.__adapter.mountsFaker.convertToLocalPath(url))

    @pyqtSlot(str, str)
    def saveCredentials(self, username, password):
        self.__adapterSettings.set("username", username)
        self.__adapterSettings.set("password", password)
        self.__legacySettings.setbool("autologin", True)
        self.__app.settings.save()

    @pyqtSlot("QList<QVariant>")
    def log(self, items):
        print("xdjs: ", end = "")
        for item in items:
            print(item, end = " ")
        print("")

    @pyqtSlot(bool)
    def slotMaskOnOffChanged(self, maskon):
        self.isPageMaskOn = maskon

    @pyqtSlot(bool)
    def slotSetOnline(self, online):
        self.isPageOnline = online

    @pyqtSlot(bool)
    def slotSetLogined(self, logined):
        self.isPageLogined = logined

    @pyqtSlot()
    def createTask(self, reason):
        logging.info("Try to consume, because {}.".format(reason))
        if not self.isPageOnline:
            return

        if self.isPageMaskOn:
            return

        if not self.isXdjsLoaded:
            return

        if not self.isPageLogined:
            return

        try:
            creation = self.__taskCreationAgent.dequeue()
        except IndexError:
            # no actions
            return

        if creation.kind == TaskCreationType.Empty:
            return self.sigCreateTask.emit("")

        if creation.kind in (TaskCreationType.Normal,
                             TaskCreationType.Emule,
                             TaskCreationType.Magnet,
                             TaskCreationType.RemoteTorrent):
            return self.sigCreateTask.emit(creation.url)

        if creation.kind == TaskCreationType.LocalTorrent:
            self.__mainWin.page.overrideFile = creation.url
            return self.sigCreateTaskFromTorrentFile.emit()

        print("Cannot process", creation)

    @pyqtSlot()
    def slotClickBtButton(self):
        keydownEvent = QKeyEvent(QEvent.KeyPress,  # type
                                 Qt.Key_Enter,     # key
                                 Qt.NoModifier)    # modifiers

        self.__app.sendEvent(self.__mainWin.webView, keydownEvent)
        self.sigCreateTaskFromTorrentFileDone.emit()

    def getFrontendStatus(self):
        return FrontendStatus(self.isXdjsLoaded, self.isPageLogined, self.isPageOnline)

    @pyqtSlot(str, str, int, int, str)
    def onJsError(self, event, source, lineno, colno, error):
        # handle unhandled JS exceptions in PY code
        logging.error("JSError: {source}:l{lineno}:c{colno} {event}:{error}".format(**locals()))
