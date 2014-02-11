#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QApplication
import main, constants

log = print

class XwareDesktop(QApplication):
    def __init__(self, *args):
        super().__init__(*args)
        import settings
        self.settings = settings.SettingsAccessor()
        self.lastWindowClosed.connect(self.cleanUp)

        self.mainWindow = main.MainWindow(self)
        self.checkUsergroup()
        self.mainWindow.show()

    def checkUsergroup(self):
        from PyQt5.QtWidgets import QMessageBox
        import grp, getpass
        try:
            xwareGrp = grp.getgrnam("xware")
        except KeyError:
            return QMessageBox.warning(QMessageBox(None), "Xware Desktop 警告", "未在本机上找到xware用户组，需要重新安装。",
                                       QMessageBox.Ok, QMessageBox.Ok)

        xwareMembers = xwareGrp[3]
        if getpass.getuser() not in xwareMembers:
            return QMessageBox.warning(QMessageBox(None), "Xware Desktop 警告", "当前用户不在xware用户组。",
                                       QMessageBox.Ok, QMessageBox.Ok)


    @pyqtSlot()
    def cleanUp(self):
        print("cleanup")

if __name__ == "__main__":
    import os
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    tasks = sys.argv[1:]
    import fcntl
    fd = os.open(constants.FRONTEND_LOCK, os.O_RDWR | os.O_CREAT, mode = 0o666)

    import ipc
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        if len(tasks) == 0:
            print("You already have an Xware Desktop instance running.")
            exit(-1)
        else:
            print(tasks)
            ipc.FrontendCommunicationClient(tasks)
            exit(0)


    app = XwareDesktop(sys.argv)
    sys.exit(app.exec())
