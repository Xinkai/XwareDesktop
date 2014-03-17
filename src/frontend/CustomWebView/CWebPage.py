# -*- coding: utf-8 -*-

from PyQt5.QtCore import QUrl
from PyQt5.QtWebKitWidgets import QWebPage

import os
from urllib import parse

from .CNetworkAccessManager import CustomNetworkAccessManager

class CustomWebPage(QWebPage):
    _overrideFile = None
    _networkAccessManager = None

    def __init__(self, parent):
        super().__init__(parent)
        self._networkAccessManager = CustomNetworkAccessManager()
        self.setNetworkAccessManager(self._networkAccessManager)
        self.applyCustomStyleSheet()

    def chooseFile(self, parentFrame, suggestFile):
        print("custom page::chooseFile", parentFrame, suggestFile)
        if self._overrideFile:
            return self.overrideFile
        else:
            return super().chooseFile(parentFrame, suggestFile)

    @property
    def overrideFile(self):
        print("read overrideFile, then clear it.")
        result = self._overrideFile
        self._overrideFile = None
        return result

    @overrideFile.setter
    def overrideFile(self, url):
        self._overrideFile = url
        print("set local torrent {}.".format(url))

    def applyCustomStyleSheet(self):
        styleSheet = QUrl(os.path.join(os.getcwd(), "style.css"))
        styleSheet.setScheme("file")
        self.settings().setUserStyleSheetUrl(styleSheet)

    def urlMatch(self, against):
        return parse.urldefrag(self.mainFrame().url().toString())[0] == against

    def urlMatchIn(self, *againsts):
        return parse.urldefrag(self.mainFrame().url().toString())[0] in againsts
