# -*- coding: utf-8 -*-

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
import constants

# Together with xwarejs.js, exchange information with the browser
class XwarePy(QObject):
    sigCreateTasks = pyqtSignal(list)
    sigLogin = pyqtSignal(str, str)

    def __init__(self, window):
        super().__init__()
        self.jsLoaded = False
        self.window = window
        print("XwarePy instance born!")

    ################################### SLOTS ######################################
    @pyqtSlot()
    def xdjsLoaded(self):
        self.jsLoaded = True
        print("xdjs loaded.")

        from urllib import parse
        if parse.urldefrag(self.window.url)[0] == constants.LOGIN_PAGE and \
            (self.window.setting.get("account", "autologin", "True") == "True"):
            self.sigLogin.emit(self.window.setting.get("account", "username"),
                               self.window.setting.get("account", "password"))

    @pyqtSlot()
    def requestFocus(self):
        self.window.frame.setFocus()