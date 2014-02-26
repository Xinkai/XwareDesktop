# -*- coding: utf-8 -*-

from PyQt5.QtCore import QUrl, pyqtSlot, QEvent
from PyQt5.QtWidgets import QMainWindow, QLabel, QSystemTrayIcon, QMenu
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.Qt import Qt

from frontendpy import FrontendPy
import constants
import ipc
from ui_main import Ui_MainWindow

log = print

class MainWindow(QMainWindow, Ui_MainWindow):
    app = None
    savedWindowState = Qt.WindowNoState

    def __init__(self, app):
        super().__init__()
        self.app = app
        ipc.FrontendCommunicationListener(self)

        self.frontendpy = FrontendPy(self) # setup Webkit Bridge
        # UI
        self.setupUi(self)
        self.setupSystray()
        self.setupStatusBar()
        self.connectUI()
        self.app.sigFrontendUiSetupFinished.emit()

        self.setupWebkit()

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

        devToolsOn = self.settings.getbool("frontend", "enabledeveloperstools")
        self.webView.settings().setAttribute(QWebSettings.DeveloperExtrasEnabled, devToolsOn)
        if devToolsOn:
            self.webView.setContextMenuPolicy(Qt.DefaultContextMenu)
        else:
            self.webView.setContextMenuPolicy(Qt.NoContextMenu)

    @pyqtSlot()
    def toggleFlash(self):
        from PyQt5.QtWebKit import QWebSettings

        allowed = self.settings.getbool("frontend", "allowflash")
        self.webView.settings().setAttribute(QWebSettings.PluginsEnabled, allowed)
        self.frontendpy.sigToggleFlashAvailability.emit(allowed)


    def connectUI(self):
        # connect UI related signal/slot
        self.action_exit.triggered.connect(self.slotExit)
        self.action_setting.triggered.connect(self.slotSetting)

        self.action_createTask.triggered.connect(self.slotPrepareTasksCreation)
        self.action_refreshPage.triggered.connect(self.slotRefreshPage)
        self.action_activateDevice.triggered.connect(lambda: self.frontendpy.sigActivateDevice.emit())

        self.action_ETMstart.triggered.connect(self.xwaredpy.slotStartETM)
        self.action_ETMstop.triggered.connect(self.xwaredpy.slotStopETM)
        self.action_ETMrestart.triggered.connect(self.xwaredpy.slotRestartETM)

        self.action_showAbout.triggered.connect(self.slotShowAbout)

    def setupSystray(self):
        self.trayIconMenu = QMenu(self)

        icon = QIcon()
        icon.addPixmap(QPixmap(":/image/thunder.ico"), QIcon.Normal, QIcon.Off)
        self.trayIconMenu.addAction(self.action_exit)

        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setIcon(icon)
        self.trayIcon.setContextMenu(self.trayIconMenu)
        self.trayIcon.setVisible(True)

        self.trayIcon.activated.connect(self.slotActivateSystrayContextMenu)

        # self.visibilityChanged.connect(self.slotVisibilityChanged)

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
        return self.qurl.url()

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
    def slotAddJSObject(self):
        self.frame.addToJavaScriptWindowObject("xdpy", self.frontendpy)

    @pyqtSlot()
    @pyqtSlot(str)
    @pyqtSlot(list)
    def slotPrepareTasksCreation(self, tasks = None):
        if tasks is None:
            self.frontendpy.sigCreateTasks.emit([""])
        else:
            if type(tasks) is str:
                self.frontendpy.sigCreateTasks.emit([tasks])
            else:
                self.frontendpy.sigCreateTasks.emit(tasks)

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
        self.settingsDialog = SettingsDialog(self)
        self.settingsDialog.exec()
        del self.settingsDialog

    # def _printDomainCookies(self):
    #     from PyQt5.QtCore import QUrl
    #     cookieJar = self.webView.page().networkAccessManager().cookieJar()
    #     for cookie in cookieJar.cookiesForUrl(QUrl("http://yuancheng.xunlei.com/")):
    #         print(bytes(cookie.name()).decode('utf-8'), bytes(cookie.value()).decode('utf-8'))

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
                if self.isVisible():
                    self.setWindowState(Qt.WindowMinimized)
                else:
                    self.setVisible(True)
                    self.setWindowState(self.savedWindowState)
            else:
                if self.isMinimized():
                    self.setWindowState(self.savedWindowState)
                else:
                    self.setWindowState(Qt.WindowMinimized)

    def changeEvent(self, qEvent):
        if qEvent.type() == QEvent.WindowStateChange:
            if self.windowState() & Qt.WindowMinimized:
                if self.settings.getbool("frontend", "minimizetosystray"):
                    self.setVisible(False)
                self.savedWindowState = qEvent.oldState()
