# -*- coding: utf-8 -*-

from PyQt5.QtCore import QUrl, pyqtSlot, QEvent
from PyQt5.QtWidgets import QMainWindow, QLabel, QSystemTrayIcon, QMenu
from PyQt5.QtGui import QIcon, QWindowStateChangeEvent
from PyQt5.Qt import Qt

from frontendpy import FrontendPy
import constants
from misc import debounce
from ui_main import Ui_MainWindow

log = print

class CustomStatusBarLabel(QLabel):
    def __init__(self, parent):
        super().__init__(parent)
        self.setTextFormat(Qt.RichText)
        parent.addPermanentWidget(self)

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

    def setupWebkit(self):
        self.settings.applySettings.connect(self.applySettingsToWebView)

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
        self.statusBar_main.xwaredStatus = CustomStatusBarLabel(self.statusBar_main)
        self.statusBar_main.etmStatus = CustomStatusBarLabel(self.statusBar_main)
        self.statusBar_main.frontendStatus = CustomStatusBarLabel(self.statusBar_main)

        sp = self.statusBar_main.frontendStatus.sizePolicy()
        sp.setHorizontalStretch(1)
        self.statusBar_main.frontendStatus.setSizePolicy(sp)

        self.statusBar_main.dlStatus = CustomStatusBarLabel(self.statusBar_main)
        self.statusBar_main.ulStatus = CustomStatusBarLabel(self.statusBar_main)

        self.xwaredpy.sigXwaredStatusPolled.connect(self.slotXwaredStatusPolled)
        self.xwaredpy.sigETMStatusPolled.connect(self.slotETMStatusPolled)
        self.frontendpy.sigFrontendStatusChanged.connect(self.slotFrontendStatusChanged)
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
    def slotXwaredStatusPolled(self, enabled):
        self.menu_backend.setEnabled(enabled)
        if enabled:
            self.statusBar_main.xwaredStatus.setText(
                "<img src=':/image/check.png' width=14 height=14><font color='green'>xwared</font>")
            self.statusBar_main.xwaredStatus.setToolTip("<div style='color:green'>xwared运行中</div>")
        else:
            self.statusBar_main.xwaredStatus.setText(
                "<img src=':/image/attention.png' width=14 height=14><font color='red'>xwared</font>")
            self.statusBar_main.xwaredStatus.setToolTip("<div style='color:red'>xwared未启动</div>")

    @pyqtSlot()
    def slotETMStatusPolled(self):
        enabled = self.xwaredpy.etmStatus

        self.action_ETMstart.setEnabled(not enabled)
        self.action_ETMstop.setEnabled(enabled)
        self.action_ETMrestart.setEnabled(enabled)

        overallCheck = False
        tooltips = []
        if enabled:
            activationStatus = self.etmpy.getActivationStatus()
            tooltips.append("<div style='color:green'>ETM运行中</div>")
            if activationStatus.status == 1:
                overallCheck = True
                tooltips.append(
                    "<div style='color:green'>"
                        "<img src=':/image/connected.png' width=16 height=16>"
                    "设备已激活</div>")
            else:
                tooltips.append(
                    "<div style='color:red'>"
                        "<img src=':/image/disconnected.png' width=16 height=16>"
                    "设备未激活</div>")
        else:
            tooltips.append("<div style='color:red'>ETM未启动</div>")

        if overallCheck:
            self.statusBar_main.etmStatus.setText(
                    "<img src=':/image/check.png' width=14 height=14><font color='green'>ETM</font>")
        else:
            self.statusBar_main.etmStatus.setText(
                "<img src=':/image/attention.png' width=14 height=14><font color='red'>ETM</font>")

        self.statusBar_main.etmStatus.setToolTip("".join(tooltips))

    @pyqtSlot()
    @debounce(0.5, instant_first = True)
    def slotFrontendStatusChanged(self):
        frontendStatus = self.frontendpy.getFrontendStatus()
        if all(frontendStatus):
            self.statusBar_main.frontendStatus.setText(
                "<img src=':/image/check.png' width=14 height=14><font color='green'>前端</font>")
        else:
            self.statusBar_main.frontendStatus.setText(
                "<img src=':/image/attention.png' width=14 height=14><font color='red'>前端</font>")

        self.statusBar_main.frontendStatus.setToolTip(
            "<div style='color:{}'>页面代码已插入</div>\n"
            "<div style='color:{}'>设备已登录</div>\n"
            "<div style='color:{}'>设备在线</div>".format(*map(lambda s: "green" if s else "red",
                                                              frontendStatus)))
        print(frontendStatus)

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
