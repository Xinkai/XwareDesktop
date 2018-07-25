# -*- coding: utf-8 -*-

import os
import logging
from launcher import app
from PyQt5.QtCore import QUrl, pyqtSlot, pyqtSignal, Qt,QVariant
from PyQt5.QtWebChannel import QWebChannel
#from PyQt5.QtWebKitWidgets import QWebPage
from PyQt5.QtWebEngineWidgets import QWebEnginePage
from PyQt5.QtWebEngineWidgets import QWebEngineScript
from PyQt5.QtWebEngineWidgets import QWebEngineProfile
from shared.misc import tryMkdir
#from PyQt5.QtWebEngineWidgets import QWebEngineSettings
from urllib import parse
import constants
from .CNetworkAccessManager import CustomNetworkAccessManager


class CustomWebPage(QWebEnginePage):
    def __init__(self, parent):
        self.myprofile = self.getProfile()
        super().__init__(self.myprofile,parent)
        self.profile=self.myprofile
        self.jsReturned=False
        self.channel=None
        self._overrideFile = None
        #self.applyCustomStyleSheet()
        self.loadStarted.connect(self.slotFrameLoadStarted)
        self.urlChanged.connect(self.slotUrlChanged, Qt.QueuedConnection)
        self.loadFinished.connect(self.injectXwareDesktop)
        app.sigMainWinLoaded.connect(self.connectUI)
        self.javaScriptConsoleMessage(QWebEnginePage.InfoMessageLevel, 'Info', 0, 'Error')
    sigFrameLoadStarted = pyqtSignal()

    @pyqtSlot()
    def connectUI(self):
        app.mainWin.action_refreshPage.triggered.connect(self.slotRefreshPage)

    # Local Torrent File Chooser Support
    def chooseFile(self, parentFrame, suggestFile):
        if self._overrideFile:
            return self.overrideFile
        else:
            return super().chooseFile(parentFrame, suggestFile)

    @property
    def overrideFile(self):
        result = self._overrideFile
        self._overrideFile = None
        return result

    @overrideFile.setter
    def overrideFile(self, url):
        self._overrideFile = url

    def urlMatchIn(self, *againsts):
        return parse.urldefrag(self.url().toString())[0] in againsts
    # Local Torrent File Chooser Support Ends Here

    def applyCustomStyleSheet(self):
        styleSheet = QUrl.fromLocalFile(constants.XWARESTYLE_FILE)
        self.setHtml("U",styleSheet)

    # mainFrame functions
    @pyqtSlot()
    def slotFrameLoadStarted(self):
        self.overrideFile = None
        self.sigFrameLoadStarted.emit()

    @pyqtSlot()
    def slotUrlChanged(self):
        if self.urlMatchIn(constants.V2_PAGE):
            logging.info("webView: redirect to V3.")
            self.triggerAction(QWebEnginePage.Stop)
            self.load(QUrl(constants.V3_PAGE))
        elif self.urlMatchIn(constants.V3_PAGE, constants.LOGIN_PAGE):
            pass
        else:
            logging.error("Unable to handle {}".format(self.url().toString()))

    def addobject(self):
        if app is not None:
            if self.channel is None:
                self.channel = QWebChannel()
            self.channel.registerObject('xdpy1', app.frontendpy)
            self.setWebChannel(self.channel)

    def addobject(self,name):
        if app is not None:
            if self.channel is None:
                self.channel = QWebChannel()
            self.channel.registerObject(name, app.frontendpy)
            self.setWebChannel(self.channel)

    @pyqtSlot()
    def blockUpdates(self):
        print('blockUpdates')
    def getProfile(self):

        path = constants.QWEBENGINECACHE_PATH
        tryMkdir(path)
        profile = QWebEngineProfile()
        profile.setCachePath(path)
        profile.clearHttpCache()
        jsFile = constants.QTWEBCHANNELJS_FILE
        with open(jsFile, encoding="UTF-8") as file:
            js = file.read()
        script = QWebEngineScript()
        script.setSourceCode(js)
        script.setName('qwebchannel.js')
        script.setInjectionPoint(QWebEngineScript.DocumentCreation)
        script.setWorldId(QWebEngineScript.MainWorld)
        script.setRunsOnSubFrames(False)
        profile.scripts().insert(script)
        return profile

    @pyqtSlot("QList<QVariant>")
    def js_callback(self, result):
        if result is not None:
            callBackResult = result
            print("js_callback:{}".format(result))
        self.jsReturned = True

    def injectJs(self,source,name):
        js = QWebEngineScript()
        js.setName(name)
        js.setSourceCode(source)
        js.setInjectionPoint(QWebEngineScript.DocumentCreation)
        js.setWorldId(QWebEngineScript.MainWorld)
        js.setRunsOnSubFrames(True)
        self.scripts().insert(js)

    def getUrl(self):
        if self.urlMatchIn(constants.LOGIN_PAGE):
            jsCode = 'document.getElementsByTagName("iFrame").item(0).src'
            self.runJavaScript(jsCode, self.js_callback)
        elif self.urlMatchIn(constants.V3_PAGE):
            print('False!')

    @pyqtSlot(bool)
    def injectXwareDesktop(self, ok):
        if not ok:  # terminated prematurely
            return
        js_prifx = '\nnew QWebChannel(qt.webChannelTransport, function(channel){window.xdpy=channel.objects.xdpy;\n'
        js_suffix = '\n})\n'

        if self.urlMatchIn(constants.LOGIN_PAGE):
            jsFile = constants.XWAREJS_LOGIN_FILE
        else:
            jsFile = constants.XWAREJS_FILE

        self.addobject('xdpy')
        with open(jsFile, encoding="UTF-8") as file:
            js = file.read()
        js_main = js_prifx+js+js_suffix
        self.runJavaScript(js_main, self.js_callback)

    @pyqtSlot()
    def slotRefreshPage(self):
        self.load(QUrl(constants.V3_PAGE))
