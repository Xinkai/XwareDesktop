#!/usr/bin/python3 -OO
# -*- coding: utf-8 -*-

import os, sys
if sys.platform == "linux":
    if os.getuid() == 0:
        print("拒绝以root执行。", file = sys.stderr)
        sys.exit(1)

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../"))
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../shared/thirdparty"))

if __name__ == "__main__":
    import faulthandler, logging
    from logging import handlers
    from utils import misc
    misc.tryMkdir(os.path.expanduser("~/.xware-desktop"))

    loggingHandler = logging.handlers.RotatingFileHandler(
        os.path.expanduser("~/.xware-desktop/log.txt"),
        maxBytes = 1024 * 1024 * 5,
        backupCount = 5)
    logging.basicConfig(handlers = (loggingHandler,),
                        format = "%(asctime)s %(levelname)s:%(name)s:%(message)s")

    faultLogFd = open(os.path.expanduser('~/.xware-desktop/frontend.fault.log'), 'a')
    faulthandler.enable(faultLogFd)

    from CrashReport import CrashAwareThreading
    CrashAwareThreading.installCrashReport()
    CrashAwareThreading.installThreadExceptionHandler()
    CrashAwareThreading.installEventLoopExceptionHandler()

from PyQt5.QtCore import pyqtSlot, pyqtSignal
from PyQt5.QtCore import QtMsgType, QMessageLogContext, QtDebugMsg, QtWarningMsg, QtCriticalMsg, \
    QtFatalMsg, qInstallMessageHandler
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont, QIcon

from shared import __version__, DATE

import constants
__all__ = ['app']


class XwareDesktop(QApplication):
    sigMainWinLoaded = pyqtSignal()
    applySettings = pyqtSignal()
    toggleMinimized = pyqtSignal()

    def __init__(self, *args):
        super().__init__(*args)
        logging.info("XWARE DESKTOP STARTS")
        self.setApplicationName("XwareDesktop")
        self.setApplicationVersion(__version__)
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        self.checkOneInstance()

        font = QFont()
        font.setPointSize(10)
        self.setFont(font)

        QIcon.setThemeName("")  # Compat for Ubuntu 14.04: A magical fix for #102

        from Settings import DEFAULT_SETTINGS
        from shared.config import SettingsAccessorBase
        self.settings = SettingsAccessorBase(constants.FRONTEND_CONFIG_FILE,
                                             DEFAULT_SETTINGS)
        self.aboutToQuit.connect(lambda: self.settings.save())

        from models import TaskModel, AdapterManager, ProxyModel

        self.taskModel = TaskModel()
        self.proxyModel = ProxyModel()
        self.proxyModel.setSourceModel(self.taskModel)

        self.adapterManager = AdapterManager(self)
        for name, item in self.settings.itr_sections_with_prefix("adapter"):
            self.adapterManager.loadAdapter(item)

        # components
        from Services import SessionService
        self.sessionService = SessionService(self)

        from Widgets.systray import Systray
        from Notify import Notifier
        from Schedule.model import SchedulerModel
        from Tasks.action import TaskCreationAgent

        self.systray = Systray(self)
        self.notifier = Notifier(self)
        self.schedulerModel = SchedulerModel(self)
        self.schedulerModel.setSourceModel(self.taskModel)
        self.taskCreationAgent = TaskCreationAgent(self)
        self.monitorWin = None
        self.applySettings.connect(self.slotCreateCloseMonitorWindow)

        # Legacy parts
        from legacy import main
        from legacy.frontendpy import FrontendPy
        self.frontendpy = FrontendPy(self)
        self.mainWin = main.MainWindow(None)
        self.mainWin.show()
        self.sigMainWinLoaded.emit()

        self.applySettings.emit()

        upgradeGuide = None
        if self.settings.get("internal", "previousversion") == "0.8":
            # upgraded or fresh installed
            upgradeGuide = "https://github.com/Xinkai/XwareDesktop/wiki/使用说明"
        else:
            previousdate = self.settings.getfloat("internal", "previousdate")
            if previousdate == 0:  # upgrade from pre-0.12
                upgradeGuide = "https://github.com/Xinkai/XwareDesktop/wiki/升级到0.12"

        if upgradeGuide:
            from PyQt5.QtCore import QUrl
            from PyQt5.QtGui import QDesktopServices
            QDesktopServices.openUrl(QUrl(upgradeGuide))

        self.settings.set("internal", "previousversion", __version__)
        self.settings.setfloat("internal", "previousdate", DATE)

    @staticmethod
    def checkOneInstance():
        fd = os.open(constants.FRONTEND_LOCK, os.O_RDWR | os.O_CREAT)

        alreadyRunning = False
        if os.name == "posix":
            import fcntl
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                alreadyRunning = True
        elif os.name == "nt":
            import msvcrt
            try:
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            except PermissionError:
                alreadyRunning = True
        else:
            raise NotImplementedError("Xware Desktop doesn't support {}".format(os.name))

        if alreadyRunning:
            def showStartErrorAndExit():
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(None, "Xware Desktop 启动失败",
                                    "Xware Desktop已经运行，或其没有正常退出。\n"
                                    "请检查：\n"
                                    "    1. 没有Xware Desktop正在运行\n"
                                    "    2. 上次运行的Xware Desktop没有残留"
                                    "（使用进程管理器查看名为python3或xware-desktop或launcher.py的进程）\n",
                                    QMessageBox.Ok, QMessageBox.Ok)
                sys.exit(-1)

            tasks = sys.argv[1:]
            if len(tasks) == 0:
                showStartErrorAndExit()
            else:
                from Tasks import CommandlineClient
                try:
                    CommandlineClient(tasks)
                except FileNotFoundError:
                    showStartErrorAndExit()
                except ConnectionRefusedError:
                    showStartErrorAndExit()
                sys.exit(0)

    @pyqtSlot()
    def slotCreateCloseMonitorWindow(self):
        logging.debug("slotCreateCloseMonitorWindow")
        show = self.settings.getbool("frontend", "showmonitorwindow")
        from Widgets import monitor
        if show:
            if self.monitorWin:
                pass  # already shown, do nothing
            else:
                self.monitorWin = monitor.MonitorWindow(None)
                self.monitorWin.show()
        else:
            if self.monitorWin:
                logging.debug("close monitorwin")
                self.monitorWin.close()
                del self.monitorWin
                self.monitorWin = None
            else:
                pass  # not shown, do nothing

    @property
    def autoStart(self):
        return os.path.lexists(constants.DESKTOP_AUTOSTART_FILE)

    @autoStart.setter
    def autoStart(self, on):
        if on:
            # mkdir if autostart dir doesn't exist
            misc.tryMkdir(os.path.dirname(constants.DESKTOP_AUTOSTART_FILE))

            misc.trySymlink(constants.DESKTOP_FILE,
                            constants.DESKTOP_AUTOSTART_FILE)
        else:
            misc.tryRemove(constants.DESKTOP_AUTOSTART_FILE)


def doQtIntegrityCheck():
    if os.path.lexists("/usr/bin/qt.conf"):
        # Detect 115wangpan, see #80
        import tkinter as tk
        import tkinter.ttk as ttk

        class QtIntegrityAlert(ttk.Frame):
            def __init__(self, master):
                super().__init__(master)
                self.pack(expand = True)

                url = "http://www.ubuntukylin.com/ukylin/forum.php?mod=viewthread&tid=9508"
                self.mainText = ttk.Label(
                    self,
                    font = ("Sans Serif", 12),
                    text = """检测到系统中可能安装了115网盘。它会导致Xware Desktop和其它的基于Qt的程序无法使用。请

* 卸载115网盘 或
* 按照{url}的方法解决此问题
""".format(url = url))
                self.mainText.pack(side = "top", fill = "both", expand = True, padx = 20,
                                   pady = (25, 0))

                self.viewThreadBtn = ttk.Button(
                    self,
                    text = "我要保留115网盘，查看解决方法",
                    command = lambda: os.system("xdg-open '{}'".format(url)))
                self.viewThreadBtn.pack(side = "bottom", fill = "none", expand = True, pady = 10)

                self.closeBtn = ttk.Button(
                    self,
                    text = "我要卸载115网盘，关闭这个窗口",
                    command = lambda: root.destroy())
                self.closeBtn.pack(side = "bottom", fill = "none", expand = True, pady = 10)

        root = tk.Tk()
        root.title("Xware Desktop 提示")
        tkapp = QtIntegrityAlert(master = root)
        sys.exit(tkapp.mainloop())


def QtMsgHandler(msgType: QtMsgType, context: QMessageLogContext, msg: str):
    strType = {
        QtDebugMsg: "DEBUG",
        QtWarningMsg: "WARN",
        QtCriticalMsg: "CRITICAL",
        QtFatalMsg: "FATAL"
    }[msgType]

    print("Qt[{strType}] {category} {function} in {file}, on line {line}\n"
          "    {msg}".format(strType = strType,
                             category = context.category,
                             function = context.function,
                             file = context.file,
                             line = context.line,
                             msg = msg),
          file = sys.stdout if msgType in (QtDebugMsg, QtWarningMsg) else sys.stderr)


app = None
if __name__ == "__main__":
    doQtIntegrityCheck()
    qInstallMessageHandler(QtMsgHandler)

    from shared.profile import profileBootstrap
    profileBootstrap(constants.PROFILE_DIR)
    app = XwareDesktop(sys.argv)

    def safeExec(app_):
        code = app_.exec()
        if __debug__:
            windows = app_.topLevelWindows()
            if windows:
                raise RuntimeError("Windows left: {}"
                                   .format(list(map(lambda win: win.objectName(),
                                                    windows))))
            widgets = app_.topLevelWidgets()
            if widgets:
                raise RuntimeError("Widgets left: {}"
                                   .format(list(map(lambda wid: wid.objectName(),
                                                    widgets))))
        del app_
        sys.exit(code)
    safeExec(app)
else:
    app = QApplication.instance()
