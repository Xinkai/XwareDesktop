# -*- coding: utf-8 -*-

import os
from urllib import parse
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QUrl, QVariant
import constants

# Together with xwarejs.js, exchange information with the browser
class FrontendPy(QObject):
    sigCreateTasks = pyqtSignal("QStringList")
    sigLogin = pyqtSignal(str, str)
    sigToggleFlashAvailability = pyqtSignal(bool)
    sigActivateDevice = pyqtSignal(str)
    sigMaskOnOffChanged = pyqtSignal(bool)

    def __init__(self, mainWin):
        super().__init__(mainWin)
        self.mainWin = mainWin
        self.mainWin.settings.applySettings.connect(self.tryLogin)

        self.page_maskon = None
        self.page_device_online = None

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

    @pyqtSlot(QVariant)
    def xdjsLoaded(self, payload):
        print("xdjs loaded")
        self.tryLogin()
        self.tryActivate(payload)

    @pyqtSlot()
    def requestFocus(self):
        self.mainWin.frame.setFocus()

    @pyqtSlot(str)
    def systemOpen(self, url):
        from PyQt5.QtGui import QDesktopServices
        url = self.mainWin.mountsFaker.convertToNativePath(url)
        qurl = QUrl(url)
        qurl.setScheme("file")
        QDesktopServices.openUrl(qurl)

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
        self.page_mask_on = val
        self.sigMaskOnOffChanged.emit(val)

