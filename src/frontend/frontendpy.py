# -*- coding: utf-8 -*-

import os
from urllib import parse
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QUrl, QVariant
import constants, actions
from actions import FrontendActionsQueue

# Together with xwarejs.js, exchange information with the browser
class FrontendPy(QObject):
    sigCreateTasks = pyqtSignal("QStringList")
    sigLogin = pyqtSignal(str, str)
    sigToggleFlashAvailability = pyqtSignal(bool)
    sigActivateDevice = pyqtSignal(str)
    sigNotifyPeerId = pyqtSignal(str) # let xdjs knows peerid

    queue = None
    mainWin = None
    isPageMaskOn = None
    isPageOnline = None
    isPageLogined = None
    isXdjsLoaded = None

    def __init__(self, mainWin):
        super().__init__(mainWin)
        self.queue = FrontendActionsQueue(self)
        self.mainWin = mainWin
        self.mainWin.settings.applySettings.connect(self.tryLogin)

        styleSheet = QUrl(os.path.join(os.getcwd(), "style.css"))
        styleSheet.setScheme("file")
        self.mainWin.app.sigFrontendUiSetupFinished.connect(lambda: \
            self.mainWin.webView.settings().setUserStyleSheetUrl(styleSheet))

        print("frontendpy loaded")

    def urlMatch(self, against):
        return parse.urldefrag(self.mainWin.url)[0] == against

    ################################### SLOTS ######################################
    @pyqtSlot()
    def tryLogin(self):
        if self.urlMatch(constants.LOGIN_PAGE):
            autologin = self.mainWin.settings.getbool("account", "autologin")
            if autologin:
                username = self.mainWin.settings.get("account", "username")
                password = self.mainWin.settings.get("account", "password")
                if username and password:
                    self.sigLogin.emit(username, password)

    def tryActivate(self, payload):
        if not self.urlMatch(constants.V3_PAGE):
            return # not v3 page

        if not payload["userid"]:
            return # not logged in

        userid, status, code, peerid = self.mainWin.etmpy.getActivationStatus()

        if userid == 0:
            # unbound
            if status == -1:
                QMessageBox.warning(self.mainWin, "Xware Desktop 警告", "ETM未启用，无法激活。需要启动ETM后，刷新页面。",
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
                QMessageBox.warning(self.mainWin, "Xware Desktop 警告", "登录的迅雷账户不是绑定的迅雷账户。",
                                    QMessageBox.Ok, QMessageBox.Ok)
                return

            elif peerid not in payload["peerids"]:
                QMessageBox.warning(self.mainWin, "Xware Desktop 警告", "前端尚未出现绑定的设备，请稍侯刷新。",
                                    QMessageBox.Ok, QMessageBox.Ok)
                return
            else:
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
        url = self.mainWin.mountsFaker.convertToNativePath(url)
        qurl = QUrl(url)
        qurl.setScheme("file")
        QDesktopServices().openUrl(qurl)

    @pyqtSlot(str, str)
    def saveCredentials(self, username, password):
        self.mainWin.settings.set("account", "username", username)
        self.mainWin.settings.set("account", "password", password)
        self.mainWin.settings.setbool("account", "autologin", True)
        self.mainWin.settings.save()

    @pyqtSlot(str)
    def log(self, *args):
        print("xdjs:", *args)

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
                pass
                # TODO

