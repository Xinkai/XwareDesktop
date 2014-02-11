# -*- coding: utf-8 -*-

from PyQt5.QtCore import QUrl, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QMainWindow, QLabel
from ui_main import Ui_MainWindow
from systemtray import Ui_SystemTray
from xwaredpy import XwaredPy
from xwarepy import XwarePy
import constants
import mounts
import ipc

log = print

class MainWindow(QMainWindow, Ui_MainWindow, Ui_SystemTray):
    UiSetupFinished = pyqtSignal()

    def __init__(self, app):
        super().__init__()
        ipc.FrontendCommunicationListener(self)
        self.app = app
        self.settings = self.app.settings

        # components
        self.xdpy = XwarePy(self) # setup Webkit Bridge
        self.xwaredpy = XwaredPy(self)

        # UI
        self.setupUi(self)
        self.setupSystray()
        self.setupStatusBar()
        self.connectUI()
        self.UiSetupFinished.emit()

        self.setupWebkit()
        self.mountsFaker = mounts.MountsFaker()

        # Load settings
        self.settings.applySettings.emit()

    def setupWebkit(self):
        self.settings.applySettings.connect(self.toggleDevelopersTools)
        self.settings.applySettings.connect(self.toggleFlash)

        self.frame.loadFinished.connect(self.injectXwareJS)
        self.frame.javaScriptWindowObjectCleared.connect(self.slotAddJSObject)
        self.webView.urlChanged.connect(self.slotUrlChanged)

    @pyqtSlot()
    def toggleDevelopersTools(self):
        from PyQt5.QtWebKit import QWebSettings
        from PyQt5.Qt import Qt

        devToolsOn = self.settings.get("frontend", "enabledeveloperstools", "0") == "1"
        self.webView.settings().setAttribute(QWebSettings.DeveloperExtrasEnabled, devToolsOn)
        if devToolsOn:
            self.webView.setContextMenuPolicy(Qt.DefaultContextMenu)
        else:
            self.webView.setContextMenuPolicy(Qt.NoContextMenu)

    @pyqtSlot()
    def toggleFlash(self):
        from PyQt5.QtWebKit import QWebSettings

        allowed = self.settings.get("frontend", "allowflash", "1") == "1"
        self.webView.settings().setAttribute(QWebSettings.PluginsEnabled, allowed)
        self.xdpy.sigToggleFlashAvailability.emit(allowed)


    def connectUI(self):
        # connect UI related signal/slot
        self.action_exit.triggered.connect(self.slotExit)
        self.action_setting.triggered.connect(self.slotSetting)

        self.action_createTask.triggered.connect(self.slotPrepareTasksCreation)
        self.action_refreshPage.triggered.connect(self.slotRefreshPage)
        self.action_activateDevice.triggered.connect(lambda: self.xdpy.sigActivateDevice.emit())

        self.action_ETMstart.triggered.connect(self.xwaredpy.slotStartETM)
        self.action_ETMstop.triggered.connect(self.xwaredpy.slotStopETM)
        self.action_ETMrestart.triggered.connect(self.xwaredpy.slotRestartETM)

        self.xwaredpy.sigXwaredStatusChanged.connect(self.slotXwaredStatusChanged)
        self.xwaredpy.sigETMStatusChanged.connect(self.slotETMStatusChanged)

        self.action_showAbout.triggered.connect(self.slotShowAbout)

    def setupStatusBar(self):
        ETMstatus = QLabel(self.statusBar)
        ETMstatus.setObjectName("label_ETMstatus")
        ETMstatus.setText("<font color=''></font>")
        self.statusBar.ETMstatus = ETMstatus
        self.statusBar.addPermanentWidget(ETMstatus)

        xwaredStatus = QLabel(self.statusBar)
        xwaredStatus.setObjectName("label_xwaredStatus")
        xwaredStatus.setText("<font color=''></font>")
        self.statusBar.xwaredStatus = xwaredStatus
        self.statusBar.addPermanentWidget(xwaredStatus)


    # shorthand
    @property
    def page(self):
        return self.webView.page()

    @property
    def frame(self):
        return self.webView.page().mainFrame()

    @property
    def qurl(self):
        return self.webView.url()

    @property
    def url(self):
        return self.qurl.url()
    # shorthand ends

    @pyqtSlot()
    def slotAddJSObject(self):
        self.frame.addToJavaScriptWindowObject("xdpy", self.xdpy)

    @pyqtSlot()
    @pyqtSlot(str)
    @pyqtSlot(list)
    def slotPrepareTasksCreation(self, tasks = None):
        if tasks is None:
            self.xdpy.sigCreateTasks.emit([""])
        else:
            if type(tasks) is str:
                self.xdpy.sigCreateTasks.emit([tasks])
            else:
                self.xdpy.sigCreateTasks.emit(tasks)

    @pyqtSlot()
    def slotUrlChanged(self):
        from urllib import parse
        url = parse.urldefrag(self.url)[0]
        log("webView urlChanged:", url)
        if url == constants.V2_PAGE:
            log("webView: redirect to V3.")
            self.webView.stop()
            self.webView.load(QUrl(constants.V3_PAGE))
        elif url in (constants.V3_PAGE, constants.LOGIN_PAGE):
            pass
        else:
            log("Unable to handle this URL", url)

    @pyqtSlot()
    def slotRefreshPage(self):
        self.webView.load(QUrl(constants.V3_PAGE))

    @pyqtSlot()
    def slotExit(self):
        self.app.quit()

    @pyqtSlot()
    def injectXwareJS(self):
        with open("xwarejs.js") as file:
            js = file.read()

        self.frame.evaluateJavaScript(js)

    @pyqtSlot()
    def slotSetting(self):
        from settings import SettingsDialog
        settingsDialog = SettingsDialog(self)
        settingsDialog.exec()

    # def _printDomainCookies(self):
    #     from PyQt5.QtCore import QUrl
    #     cookieJar = self.webView.page().networkAccessManager().cookieJar()
    #     for cookie in cookieJar.cookiesForUrl(QUrl("http://yuancheng.xunlei.com/")):
    #         print(bytes(cookie.name()).decode('utf-8'), bytes(cookie.value()).decode('utf-8'))

    @pyqtSlot(bool)
    def slotXwaredStatusChanged(self, enabled):
        self.menu_backend.setEnabled(enabled)
        if enabled:
            self.statusBar.xwaredStatus.setText("<font color='green'>xwared运行中</font>")
        else:
            self.statusBar.xwaredStatus.setText("<font color='red'>xwared未启动</font>")

    @pyqtSlot(bool)
    def slotETMStatusChanged(self, enabled):
        self.action_ETMstart.setEnabled(not enabled)
        self.action_ETMstop.setEnabled(enabled)
        self.action_ETMrestart.setEnabled(enabled)

        if enabled:
            self.statusBar.ETMstatus.setText("<font color='green'>ETM运行中</font>")
        else:
            self.statusBar.ETMstatus.setText("<font color='red'>ETM未启动</font>")

    @pyqtSlot()
    def slotShowAbout(self):
        from about import AboutDialog
        aboutDialog = AboutDialog(self)
        aboutDialog.exec()


