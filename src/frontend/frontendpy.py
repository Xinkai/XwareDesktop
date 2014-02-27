# -*- coding: utf-8 -*-

import os
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QUrl
import constants

# Together with xwarejs.js, exchange information with the browser
class FrontendPy(QObject):
    sigCreateTasks = pyqtSignal("QStringList")
    sigLogin = pyqtSignal(str, str)
    sigToggleFlashAvailability = pyqtSignal(bool)
    sigActivateDevice = pyqtSignal()
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

    ################################### SLOTS ######################################
    @pyqtSlot()
    def tryLogin(self):
        autologin = self.mainWin.settings.getbool("account", "autologin")
        if autologin:
            username = self.mainWin.settings.get("account", "username")
            password = self.mainWin.settings.get("account", "password")
            if username and password:
                from urllib import parse
                if parse.urldefrag(self.mainWin.url)[0] == constants.LOGIN_PAGE and \
                    self.mainWin.settings.getbool("account", "autologin"):
                    self.sigLogin.emit(username, password)

    @pyqtSlot()
    def xdjsLoaded(self):
        print("xdjs loaded")
        self.tryLogin()

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

