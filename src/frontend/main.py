# -*- coding: utf-8 -*-

from PyQt5.QtCore import QUrl, pyqtSlot, QEvent, QCoreApplication
from PyQt5.QtWebKitWidgets import QWebPage
from PyQt5.QtWidgets import QMainWindow, QLabel, QSystemTrayIcon, QMenu
from PyQt5.QtGui import QIcon, QWindowStateChangeEvent
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkDiskCache
from PyQt5.Qt import Qt

from frontendpy import FrontendPy
import constants
from ui_main import Ui_MainWindow

import os
from urllib import parse

log = print

class CustomNetworkAccessManager(QNetworkAccessManager):
    _cachePath = None

    def __init__(self):
        super().__init__()

        # set cache
        self._cachePath = QNetworkDiskCache(self)
        cacheLocation = QCoreApplication.instance().settings.get("frontend", "cachelocation")
        self._cachePath.setCacheDirectory(cacheLocation)
        self._cachePath.setMaximumCacheSize(20 * 1024 * 1024) # 20M
        self.setCache(self._cachePath)

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

class MainWindow(QMainWindow, Ui_MainWindow):
    app = None
    savedWindowState = Qt.WindowNoState

    def __init__(self, app):
        super().__init__()
        self.app = app

        self.frontendpy = FrontendPy(self) # setup Webkit Bridge
        # UI
        self.setupUi(self)
        self.setupSystray()
        self.setupStatusBar()
        self.connectUI()

        self.setupWebkit()
        self.app.sigFrontendUiSetupFinished.emit()

        # Load settings
        self.settings.applySettings.emit()

    def setupWebkit(self):
        self.settings.applySettings.connect(self.applySettingsToWebView)

        self._customPage = CustomWebPage(self.webView)
        self.webView.setPage(self._customPage)
        self.frame.loadStarted.connect(self.slotFrameLoadStarted)
        self.frame.urlChanged.connect(self.slotUrlChanged)
        self.frame.loadFinished.connect(self.injectXwareDesktop)
        self.webView.load(QUrl(constants.LOGIN_PAGE))

    @pyqtSlot()
    def applySettingsToWebView(self):
        from PyQt5.QtWebKit import QWebSettings
        from PyQt5.Qt import Qt

        isDevToolsAllowed = self.settings.getbool("frontend", "enabledeveloperstools")
        self.webView.settings().setAttribute(QWebSettings.DeveloperExtrasEnabled, isDevToolsAllowed)
        if isDevToolsAllowed:
            self.webView.setContextMenuPolicy(Qt.DefaultContextMenu)
        else:
            self.webView.setContextMenuPolicy(Qt.NoContextMenu)

        pluginsAllowed = self.settings.getbool("frontend", "allowflash")
        self.webView.settings().setAttribute(QWebSettings.PluginsEnabled, pluginsAllowed)
        self.frontendpy.sigToggleFlashAvailability.emit(pluginsAllowed)

    def connectUI(self):
        # connect UI related signal/slot
        self.action_exit.triggered.connect(self.slotExit)
        self.action_setting.triggered.connect(self.slotSetting)

        self.action_createTask.triggered.connect(self.frontendpy.queue.createTasksAction)
        self.action_refreshPage.triggered.connect(self.slotRefreshPage)

        self.action_ETMstart.triggered.connect(self.xwaredpy.slotStartETM)
        self.action_ETMstop.triggered.connect(self.xwaredpy.slotStopETM)
        self.action_ETMrestart.triggered.connect(self.xwaredpy.slotRestartETM)

        self.action_showAbout.triggered.connect(self.slotShowAbout)

    def setupSystray(self):
        self.trayIconMenu = QMenu(None)

        icon = QIcon(":/image/thunder.ico")
        self.trayIconMenu.addAction(self.action_exit)

        self.trayIcon = QSystemTrayIcon(None)
        self.trayIcon.setIcon(icon)
        self.trayIcon.setContextMenu(self.trayIconMenu)
        self.trayIcon.setVisible(True)

        self.trayIcon.activated.connect(self.slotActivateSystrayContextMenu)
        self.app.lastWindowClosed.connect(self.teardownSystray)

    @pyqtSlot()
    def teardownSystray(self):
        print("teardown Systray")
        # On Ubuntu 13.10, systrayicon won't destroy itself gracefully, stops the whole program from exiting.
        del self.trayIcon

    def setupStatusBar(self):
        xwaredStatus = QLabel(self.statusBar_main)
        xwaredStatus.setObjectName("label_xwaredStatus")
        xwaredStatus.setText("<font color=''></font>")
        self.statusBar_main.xwaredStatus = xwaredStatus
        self.statusBar_main.addPermanentWidget(xwaredStatus)
        del xwaredStatus

        ETMstatus = QLabel(self.statusBar_main)
        ETMstatus.setObjectName("label_ETMstatus")
        ETMstatus.setText("<font color=''></font>")
        self.statusBar_main.ETMstatus = ETMstatus
        self.statusBar_main.addPermanentWidget(ETMstatus, 1)
        del ETMstatus

        dlStatus = QLabel(self.statusBar_main)
        dlStatus.setObjectName("label_dlStatus")
        dlStatus.setTextFormat(Qt.RichText)
        self.statusBar_main.dlStatus = dlStatus
        self.statusBar_main.addPermanentWidget(dlStatus)
        del dlStatus

        ulStatus = QLabel(self.statusBar_main)
        ulStatus.setObjectName("label_ulStatus")
        ulStatus.setTextFormat(Qt.RichText)
        self.statusBar_main.ulStatus = ulStatus
        self.statusBar_main.addPermanentWidget(ulStatus)
        del ulStatus

        self.xwaredpy.sigXwaredStatusChanged.connect(self.slotXwaredStatusChanged)
        self.xwaredpy.sigETMStatusChanged.connect(self.slotETMStatusChanged)
        self.etmpy.sigTasksSummaryUpdated[bool].connect(self.slotTasksSummaryUpdated)
        self.etmpy.sigTasksSummaryUpdated[dict].connect(self.slotTasksSummaryUpdated)

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
        # for some reason, on Ubuntu QUrl.url() is not there, call toString() instead.
        return self.qurl.toString()

    @property
    def settings(self):
        return self.app.settings

    @property
    def xwaredpy(self):
        return self.app.xwaredpy

    @property
    def etmpy(self):
        return self.app.etmpy

    @property
    def mountsFaker(self):
        return self.app.mountsFaker
    # shorthand ends

    @pyqtSlot()
    def slotUrlChanged(self):
        if self.page.urlMatch(constants.V2_PAGE):
            log("webView: redirect to V3.")
            self.webView.stop()
            self.frame.load(QUrl(constants.V3_PAGE))
        elif self.page.urlMatchIn(constants.V3_PAGE, constants.LOGIN_PAGE):
            pass
        else:
            log("Unable to handle this URL", self.url)

    @pyqtSlot()
    def slotRefreshPage(self):
        self.frame.load(QUrl(constants.V3_PAGE))

    @pyqtSlot()
    def slotExit(self):
        self.app.quit()

    @pyqtSlot()
    def slotFrameLoadStarted(self):
        self.page.overrideFile = None
        self.frontendpy.isPageMaskOn = None
        self.frontendpy.isPageOnline = None
        self.frontendpy.isPageLogined = None
        self.frontendpy.isXdjsLoaded = None

    @pyqtSlot()
    def injectXwareDesktop(self):
        # inject xdpy object
        self.frame.addToJavaScriptWindowObject("xdpy", self.frontendpy)

        # inject xdjs script
        with open("xwarejs.js") as file:
            js = file.read()
        self.frame.evaluateJavaScript(js)

    @pyqtSlot()
    def slotSetting(self):
        from settings import SettingsDialog
        self.settingsDialog = SettingsDialog(self)
        self.settingsDialog.exec()
        del self.settingsDialog

    @pyqtSlot(bool)
    def slotXwaredStatusChanged(self, enabled):
        self.menu_backend.setEnabled(enabled)
        if enabled:
            self.statusBar_main.xwaredStatus.setText(
                "<img src=':/image/check.png' width=14 height=14><font color='green'>xwared</font>")
            self.statusBar_main.xwaredStatus.setToolTip("xwared运行中")
        else:
            self.statusBar_main.xwaredStatus.setText(
                "<img src=':/image/attention.png' width=14 height=14><font color='red'>xwared</font>")
            self.statusBar_main.xwaredStatus.setToolTip("xwared未启动")

    @pyqtSlot(bool)
    def slotETMStatusChanged(self, enabled):
        self.action_ETMstart.setEnabled(not enabled)
        self.action_ETMstop.setEnabled(enabled)
        self.action_ETMrestart.setEnabled(enabled)

        if enabled:
            self.statusBar_main.ETMstatus.setText(
                "<img src=':/image/check.png' width=14 height=14><font color='green'>ETM</font>")
            self.statusBar_main.ETMstatus.setToolTip("ETM运行中")
        else:
            self.statusBar_main.ETMstatus.setText(
                "<img src=':/image/attention.png' width=14 height=14><font color='red'>ETM</font>")
            self.statusBar_main.ETMstatus.setToolTip("ETM未启动")

    @pyqtSlot()
    def slotShowAbout(self):
        from about import AboutDialog
        self.aboutDialog = AboutDialog(self)
        self.aboutDialog.exec()
        del self.aboutDialog

    @pyqtSlot(bool)
    @pyqtSlot(dict)
    def slotTasksSummaryUpdated(self, summary):
        import misc
        if not summary:
            self.statusBar_main.dlStatus.setText(
                "<img src=':/image/down.png' height=14 width=14>获取下载状态失败"
            )
            self.statusBar_main.dlStatus.setToolTip("")
            self.statusBar_main.ulStatus.setText(
                "<img src=':/image/up.png' height=14 width=14>获取上传状态失败"
            )
            return

        self.statusBar_main.dlStatus.setText(
            "<img src=':/image/down.png' height=14 width=14>{}/s".format(
                                        misc.getHumanBytesNumber(summary["dlSpeed"])))
        self.statusBar_main.dlStatus.setToolTip("{}任务下载中".format(summary["dlNum"]))
        self.statusBar_main.ulStatus.setText(
            "<img src=':/image/up.png' height=14 width=14>{}/s".format(misc.getHumanBytesNumber(summary["upSpeed"]))
        )

    @pyqtSlot(QSystemTrayIcon.ActivationReason)
    def slotActivateSystrayContextMenu(self, reason):
        if reason == QSystemTrayIcon.Context: # right
            pass
        elif reason == QSystemTrayIcon.MiddleClick: # middle
            pass
        elif reason == QSystemTrayIcon.DoubleClick: # double click
            pass
        elif reason == QSystemTrayIcon.Trigger: # left
            if self.settings.getbool("frontend", "minimizetosystray"):
                if self.isHidden():
                    self.setVisible(True)
                    self.setWindowState(self.savedWindowState)
                else:
                    self.setWindowState(Qt.WindowMinimized)
            else:
                if self.isMinimized():
                    self.setWindowState(self.savedWindowState)
                else:
                    self.setWindowState(Qt.WindowMinimized)

    @pyqtSlot(QWindowStateChangeEvent)
    def changeEvent(self, qEvent):
        if qEvent.type() == QEvent.WindowStateChange:
            if self.windowState() & Qt.WindowMinimized:
                if self.settings.getbool("frontend", "minimizetosystray"):
                    self.setVisible(False)
            else:
                # the following two lines should not be necessary.
                # without these lines, restoring from minimized can be problematic.
                # treat it as a workaround.
                if int(qEvent.oldState()) == Qt.WindowMinimized:
                    return
                self.savedWindowState = self.windowState()
