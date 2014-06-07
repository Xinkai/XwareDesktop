#!/usr/bin/python3
# -*- coding: utf-8 -*-

if __name__ == "__main__":
    import faulthandler, os, logging
    try:
        os.mkdir(os.path.expanduser("~/.xware-desktop"))
    except OSError:
        pass  # already exists

    logging.basicConfig(filename = os.path.expanduser("~/.xware-desktop/log.txt"))

    faultLogFd = open(os.path.expanduser('~/.xware-desktop/frontend.fault.log'), 'a')
    faulthandler.enable(faultLogFd)

    from CrashReport import CrashAwareThreading
    CrashAwareThreading.installCrashReport()
    CrashAwareThreading.installThreadExceptionHandler()

from PyQt5.QtCore import pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QApplication

import fcntl, os, sys
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../"))

from shared import __version__

import constants
__all__ = ['app']


class XwareDesktop(QApplication):
    mainWin = None
    monitorWin = None
    sigMainWinLoaded = pyqtSignal()

    def __init__(self, *args):
        super().__init__(*args)

        import main
        from Settings import SettingsAccessor, DEFAULT_SETTINGS
        from xwaredpy import XwaredPy
        from etmpy import EtmPy
        from systray import Systray
        import mounts
        from Notify import Notifier
        from frontendpy import FrontendPy
        from Schedule import Scheduler

        logging.info("XWARE DESKTOP STARTS")
        self.setApplicationName("XwareDesktop")
        self.setApplicationVersion(__version__)

        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        self.checkOneInstance()

        self.settings = SettingsAccessor(self,
                                         configFilePath = constants.CONFIG_FILE,
                                         defaultDict = DEFAULT_SETTINGS)

        # components
        self.xwaredpy = XwaredPy(self)
        self.etmpy = EtmPy(self)
        self.mountsFaker = mounts.MountsFaker()
        self.dbusNotify = Notifier(self)
        self.frontendpy = FrontendPy(self)
        self.scheduler = Scheduler(self)

        self.settings.applySettings.connect(self.slotCreateCloseMonitorWindow)

        self.mainWin = main.MainWindow(None)
        self.mainWin.show()
        self.sigMainWinLoaded.emit()

        self.systray = Systray(self)

        self.settings.applySettings.emit()

    @staticmethod
    def checkOneInstance():
        tasks = sys.argv[1:]

        fd = os.open(constants.FRONTEND_LOCK, os.O_RDWR | os.O_CREAT)

        from Tasks import CommandlineClient
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            if len(tasks) == 0:
                print("You already have an Xware Desktop instance running.")
                sys.exit(-1)
            else:
                print(tasks)
                CommandlineClient(tasks)
                sys.exit(0)

    @pyqtSlot()
    def slotCreateCloseMonitorWindow(self):
        logging.debug("slotCreateCloseMonitorWindow")
        show = self.settings.getbool("frontend", "showmonitorwindow")
        import monitor
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

app = None
if __name__ == "__main__":
    from shared.profile import profileBootstrap
    profileBootstrap(constants.PROFILE_DIR)
    app = XwareDesktop(sys.argv)
    sys.exit(app.exec())
else:
    app = QApplication.instance()
