# -*- coding: utf-8 -*-

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QUrl
import constants

# Together with xwarejs.js, exchange information with the browser
class XwarePy(QObject):
    sigCreateTasks = pyqtSignal("QStringList")
    sigLogin = pyqtSignal(str, str)

    def __init__(self, window):
        super().__init__()
        self.jsLoaded = False
        self.window = window
        print("xdpy loaded")

    ################################### SLOTS ######################################
    @pyqtSlot()
    def xdjsLoaded(self):
        self.jsLoaded = True
        print("xdjs loaded")

        username = self.window.setting.get("account", "username", None)
        password = self.window.setting.get("account", "password", None)

        if username and password:
            from urllib import parse
            if parse.urldefrag(self.window.url)[0] == constants.LOGIN_PAGE and \
                (self.window.setting.get("account", "autologin", "True") == "True"):
                self.sigLogin.emit(username, password)

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
