#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QApplication

import fcntl, os, sys

import main, constants, settings, monitor
from xwaredpy import XwaredPy
from etmpy import EtmPy
from systray import Systray
import mounts
from Notify import Notifier
from frontendpy import FrontendPy
from Schedule import Scheduler

log = print

class XwareDesktop(QApplication):
    mainWin = None
    monitorWin = None

    def __init__(self, *args):
        super().__init__(*args)
        logging.info("XWARE DESKTOP STARTS")
        self.setApplicationName("XwareDesktop")
        self.setApplicationVersion("0.1")

        self.checkUsergroup()

        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        self.checkOneInstance()

        self.settings = settings.SettingsAccessor(self)
        self.lastWindowClosed.connect(self.cleanUp)

        # components
        self.xwaredpy = XwaredPy(self)
        self.etmpy = EtmPy(self)
        self.mountsFaker = mounts.MountsFaker()
        self.dbusNotify = Notifier(self)
        self.frontendpy = FrontendPy(self)
        self.scheduler = Scheduler(self)

        self.settings.applySettings.connect(self.slotCreateCloseMonitorWindow)

        self.mainWin = main.MainWindow(self)
        self.mainWin.show()

        self.systray = Systray(self)

        self.settings.applySettings.emit()

    def checkOneInstance(self):
        tasks = sys.argv[1:]

        fd = os.open(constants.FRONTEND_LOCK, os.O_RDWR | os.O_CREAT, mode = 0o666)

        import actions
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            if len(tasks) == 0:
                print("You already have an Xware Desktop instance running.")
                sys.exit(-1)
            else:
                print(tasks)
                actions.FrontendCommunicationClient(tasks)
                sys.exit(0)

    def checkUsergroup(self):
        from PyQt5.QtWidgets import QMessageBox
        import grp, getpass
        try:
            xwareGrp = grp.getgrnam("xware")
        except KeyError:
            QMessageBox.warning(QMessageBox(None), "Xware Desktop 警告", "未在本机上找到xware用户组，需要重新安装。",
                                QMessageBox.Ok, QMessageBox.Ok)
            sys.exit(-1)

        xwareGid, xwareMembers = xwareGrp[2], xwareGrp[3]
        if getpass.getuser() not in xwareMembers:
            QMessageBox.warning(QMessageBox(None), "Xware Desktop 警告", "当前用户不在xware用户组。",
                                QMessageBox.Ok, QMessageBox.Ok)
            sys.exit(-1)

        currentGroups = os.getgroups()
        if xwareGid not in currentGroups:
            QMessageBox.warning(QMessageBox(None), "Xware Desktop 警告", "当前进程没有应用xware用户组，请注销并重登入。",
                                QMessageBox.Ok, QMessageBox.Ok)
            sys.exit(-1)

    @pyqtSlot()
    def cleanUp(self):
        self.xwaredpy.stopXware()
        print("cleanup")

    @pyqtSlot()
    def slotCreateCloseMonitorWindow(self):
        logging.debug("slotCreateCloseMonitorWindow")
        show = self.settings.getbool("frontend", "showmonitorwindow")
        if show:
            if self.monitorWin:
                pass # already shown, do nothing
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
                pass # not shown, do nothing

if __name__ == "__main__":
    logging.basicConfig(filename = os.path.expanduser("~/.xware-desktop/log.txt"))
    app = XwareDesktop(sys.argv)
    sys.exit(app.exec())
