#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os, sys
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../"))

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

from PyQt5.QtCore import pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QApplication

import fcntl

from shared import __version__

import constants
__all__ = ['app']


class XwareDesktop(QApplication):
    sigMainWinLoaded = pyqtSignal()

    def __init__(self, *args):
        super().__init__(*args)
        logging.info("XWARE DESKTOP STARTS")
        self.setApplicationName("XwareDesktop")
        self.setApplicationVersion(__version__)
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        self.checkOneInstance()

        from Settings import SettingsAccessor, DEFAULT_SETTINGS
        self.settings = SettingsAccessor(self,
                                         configFilePath = constants.CONFIG_FILE,
                                         defaultDict = DEFAULT_SETTINGS)

        from models import TaskModel, AdapterManager, ProxyModel
        from libxware import XwareAdapter
        self.taskModel = TaskModel()
        self.proxyModel = ProxyModel()
        self.proxyModel.setSourceModel(self.taskModel)

        self.adapterManager = AdapterManager(self)
        self.adapter = XwareAdapter({
            "host": "127.0.0.1",
            "port": 9000,
        }, parent = self)
        self.adapterManager.registerAdapter(self.adapter)

        # components
        from Widgets.systray import Systray
        from Notify import Notifier
        from Schedule.model import SchedulerModel

        self.systray = Systray(self)
        self.notifier = Notifier(self)
        self.schedulerModel = SchedulerModel(self)
        self.schedulerModel.setSourceModel(self.taskModel)
        self.monitorWin = None
        self.settings.applySettings.connect(self.slotCreateCloseMonitorWindow)

        # Legacy parts
        from legacy import main
        from legacy.frontendpy import FrontendPy
        self.frontendpy = FrontendPy(self)
        self.mainWin = main.MainWindow(None)
        self.mainWin.show()
        self.sigMainWinLoaded.emit()

        self.settings.applySettings.emit()

        if self.settings.get("internal", "previousversion") == "0.8":
            # upgraded or fresh installed
            from PyQt5.QtCore import QUrl
            from PyQt5.QtGui import QDesktopServices
            QDesktopServices.openUrl(QUrl("https://github.com/Xinkai/XwareDesktop/wiki/使用说明"))

        self.settings.set("internal", "previousversion", __version__)

    @staticmethod
    def checkOneInstance():
        fd = os.open(constants.FRONTEND_LOCK, os.O_RDWR | os.O_CREAT)

        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
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
                    font=("Sans Serif", 12),
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


app = None
if __name__ == "__main__":
    doQtIntegrityCheck()

    from shared.profile import profileBootstrap
    profileBootstrap(constants.PROFILE_DIR)
    app = XwareDesktop(sys.argv)
    sys.exit(app.exec())
else:
    app = QApplication.instance()
