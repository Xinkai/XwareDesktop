# -*- coding: utf-8 -*-

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QUrl
import constants

# Together with xwarejs.js, exchange information with the browser
class XwarePy(QObject):
    sigCreateTasks = pyqtSignal("QStringList")
    sigLogin = pyqtSignal(str, str)
    sigToggleFlashAvailability = pyqtSignal(bool)
    sigActivateDevice = pyqtSignal()

    def __init__(self, window):
        super().__init__(window)
        self.jsLoaded = False
        self.window = window
        self.window.settings.applySettings.connect(self.tryLogin)
        print("xdpy loaded")

    def tryLogin(self):
        autologin = self.window.settings.getbool("account", "autologin")
        if autologin:
            username = self.window.settings.get("account", "username")
            password = self.window.settings.get("account", "password")
            if username and password:
                from urllib import parse
                if parse.urldefrag(self.window.url)[0] == constants.LOGIN_PAGE and \
                    self.window.settings.getbool("account", "autologin"):
                    self.sigLogin.emit(username, password)

    ################################### SLOTS ######################################
    @pyqtSlot()
    def xdjsLoaded(self):
        self.jsLoaded = True
        print("xdjs loaded")

        self.tryLogin()

    @pyqtSlot()
    def requestFocus(self):
        self.window.frame.setFocus()

    @pyqtSlot(str)
    def systemOpen(self, url):
        from PyQt5.QtGui import QDesktopServices
        url = self.window.mountsFaker.convertToNativePath(url)
        qurl = QUrl(url)
        qurl.setScheme("file")
        QDesktopServices.openUrl(qurl)

    @pyqtSlot(str, str)
    def saveCredentials(self, username, password):
        self.window.settings.set("account", "username", username)
        self.window.settings.set("account", "password", password)
        self.window.settings.setbool("account", "autologin", True)
        self.window.settings.save()

    @pyqtSlot(str)
    def log(self, *args):
        print("xdjs:", *args)
