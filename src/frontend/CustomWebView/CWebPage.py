# -*- coding: utf-8 -*-

import logging
from launcher import app

from PyQt5.QtCore import QUrl, pyqtSlot
from PyQt5.QtWebKitWidgets import QWebPage

from urllib import parse

import constants
from .CNetworkAccessManager import CustomNetworkAccessManager


class CustomWebPage(QWebPage):
    _overrideFile = None
    _networkAccessManager = None

    def __init__(self, parent):
        super().__init__(parent)
        self._networkAccessManager = CustomNetworkAccessManager()
        self.setNetworkAccessManager(self._networkAccessManager)
        self.applyCustomStyleSheet()

        self.frame.loadStarted.connect(self.slotFrameLoadStarted)
        self.frame.urlChanged.connect(self.slotUrlChanged)
        self.frame.loadFinished.connect(self.injectXwareDesktop)
        app.sigMainWinLoaded.connect(self.connectUI)

    @property
    def frame(self):
        return self.mainFrame()

    @pyqtSlot()
    def connectUI(self):
        app.mainWin.action_refreshPage.triggered.connect(self.slotRefreshPage)

    # Local Torrent File Chooser Support
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

    def urlMatchIn(self, *againsts):
        return parse.urldefrag(self.frame.url().toString())[0] in againsts
    # Local Torrent File Chooser Support Ends Here

    def applyCustomStyleSheet(self):
        styleSheet = QUrl.fromLocalFile(constants.XWARESTYLE_FILE)
        self.settings().setUserStyleSheetUrl(styleSheet)

    # mainFrame functions
    @pyqtSlot()
    def slotFrameLoadStarted(self):
        self.overrideFile = None
        app.frontendpy.isPageMaskOn = None
        app.frontendpy.isPageOnline = None
        app.frontendpy.isPageLogined = None
        app.frontendpy.isXdjsLoaded = None

    @pyqtSlot()
    def slotUrlChanged(self):
        if self.urlMatchIn(constants.V2_PAGE):
            logging.info("webView: redirect to V3.")
            self.triggerAction(QWebPage.Stop)
            self.frame.load(QUrl(constants.V3_PAGE))
        elif self.urlMatchIn(constants.V3_PAGE, constants.LOGIN_PAGE):
            pass
        else:
            logging.error("Unable to handle {}".format(self.url().toString()))

    @pyqtSlot()
    def injectXwareDesktop(self):
        # inject xdpy object
        self.frame.addToJavaScriptWindowObject("xdpy", app.frontendpy)

        # inject xdjs script
        with open(constants.XWAREJS_FILE, encoding = "UTF-8") as file:
            js = file.read()
        self.frame.evaluateJavaScript(js)

    @pyqtSlot()
    def slotRefreshPage(self):
        self.frame.load(QUrl(constants.V3_PAGE))
