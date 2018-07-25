# -*- coding: utf-8 -*-
import sys
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.Qt import QApplication,QObject,QWidget,QUrl
from PyQt5.QtCore import pyqtSlot,pyqtProperty,pyqtSignal
from PyQt5.QtWebEngineWidgets import QWebEnginePage,QWebEngineScript,QWebEngineProfile,QWebEngineView
import constants

class myObject(QObject):
    def __init__(self):
        super().__init__()
    @pyqtSlot()
    def test(self):
        QMessageBox.warning(None, "Xware Desktop 警告", "ETM未启用，无法激活。需要启动ETM后，刷新页面。",
                            QMessageBox.Ok, QMessageBox.Ok)
        print("js调用成功！")

class MainWidow(QWidget):
    def __init__(self):

        super().__init__()
        self.view=QWebEngineView()
        self.myprofile=self.getProfile()
        self.page=QWebEnginePage(self.myprofile,None)

        # self.channel=QWebChannel()
        # self.myobject=myObject()
        # self.channel.registerObject("xdpy", self.myobject)
        # self.page.setWebChannel(self.channel)

        self.page.settings().AllowRunningInsecureContent=True;
        self.page.settings().JavascriptEnabled=True;
        self.view.page=self.page
        self.url=QUrl("")
        self.view.page.load(self.url)
        self.view.show()
        self.view.settings().JavascriptEnabled=True
    def js_callback(self,result):
        print("js_callback:{}".format(result))
    def injectJS(self,sourceCode,name):
        script = QWebEngineScript();
        script.setSourceCode(sourceCode)
        script.setName(name)
        script.setInjectionPoint(QWebEngineScript.DocumentCreation)
        script.setWorldId(QWebEngineScript.MainWorld)
        script.setRunsOnSubFrames(True)
        self.view.page.scripts().insert(script)
        self.page.scripts().insert(script)

    def getProfile(self):
        profile=QWebEngineProfile("myProfile")
        profile.cachePath="/home/yyk/Desktop/cache"
        jsFile = constants.QTWEBCHANNELJS_FILE
        with open(jsFile, encoding="UTF-8") as file:
            js = file.read()
        script = QWebEngineScript();
        script.setSourceCode(js)
        script.setName('qwebchannel.js')
        script.setInjectionPoint(QWebEngineScript.DocumentCreation)
        script.setWorldId(QWebEngineScript.MainWorld)
        script.setRunsOnSubFrames(False)
        profile.scripts().insert(script)
        return profile
if __name__ == "__main__":
    app=QApplication(sys.argv)
    mainwindow=MainWidow()

    url = QUrl('file:///home/yyk/Desktop/index.html')
    mainwindow.view.page.load(url)

    # jsFile = constants.QTWEBCHANNELJS_FILE
    # with open(jsFile, encoding="UTF-8") as file:
    #     js = file.read()
    # script = QWebEngineScript();
    # script.setSourceCode(js)
    # script.setName('qwebchannel.js')
    # script.setInjectionPoint(QWebEngineScript.DocumentCreation)
    # script.setWorldId(QWebEngineScript.MainWorld)
    # script.setRunsOnSubFrames(False)
    #
    # mainwindow.view.page.profile().scripts().insert(script)

    channel = QWebChannel()
    myobject=myObject()
    channel.registerObject("xdpy",myobject)
    mainwindow.view.page.setWebChannel(channel)

    #
    # jsFile = constants.QTWEBCHANNELJS_FILE
    # with open(jsFile, encoding="UTF-8") as file:
    #     js = file.read()
    # mainwindow.injectJS(js, 'qwebchannel.js')


    js='\nnew QWebChannel(qt.webChannelTransport, function(channel){alert("正在调用回调函数");window.xdpy=channel.objects.xdpy;xdpy.test();});\n'
    #mainwindow.view.page.runJavaScript(js,mainwindow.js_callback)
    # mainwindow.view.page.runJavaScript('window.channel="AAAA"', mainwindow.js_callback)
    mainwindow.view.page.runJavaScript(js,mainwindow.js_callback)
    #mainwindow.view.page.runJavaScript("window.xdpy.test()",mainwindow.js_callback)
    app.exec();