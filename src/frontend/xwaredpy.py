# -*- coding: utf-8 -*-


from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
import threading, time
import fcntl
import constants

# an interface to watch, notify, and supervise the status of xwared and ETM
class XwaredPy(QObject):
    sigXwaredStatusChanged = pyqtSignal(bool)
    sigETMStatusChanged = pyqtSignal(bool)

    def __init__(self, window):
        self.window = window
        super().__init__(self.window)
        self.startXware()
        self.xwaredStatus = None
        self.etmStatus = None
        self.window.UiSetupFinished.connect(self.watch)
        self.window.app.lastWindowClosed.connect(self.stopXware)

    def startXware(self):
        if self.window.settings.getint("xwared", "startetmwhen") == 3:
            self.slotStartETM()
            self.window.settings.setbool("xwared", "startetm", True)
            self.window.settings.save()

    def stopXware(self):
        # this method is called by XwareDesktop::cleanUp
        if self.window.settings.getint("xwared", "startetmwhen") == 3:
            self.slotStopETM()
            self.window.settings.setbool("xwared", "startetm", True)
            self.window.settings.save()

    def watch(self):
        self.t = threading.Thread(target = self._watcherThread, daemon = True)
        self.t.start()

    def _watcherThread(self):
        while True:
            try:
                xwaredLockFile = open(constants.XWARED_LOCK)
                try:
                    xwaredLock = fcntl.flock(xwaredLockFile, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    xwaredStatus = False
                    fcntl.flock(xwaredLockFile, fcntl.LOCK_UN)
                except BlockingIOError:
                    xwaredStatus = True
                xwaredLockFile.close()
            except FileNotFoundError:
                xwaredStatus = False

            if xwaredStatus != self.xwaredStatus:
                self.xwaredStatus = xwaredStatus
                self.sigXwaredStatusChanged.emit(xwaredStatus)

            try:
                etmLockFile = open(constants.ETM_LOCK)
                try:
                    etmLock = fcntl.flock(etmLockFile, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    etmStatus = False
                    fcntl.flock(etmLockFile, fcntl.LOCK_UN)
                except BlockingIOError:
                    etmStatus = True
                etmLockFile.close()
            except FileNotFoundError:
                etmStatus = False

            if etmStatus != self.etmStatus:
                self.etmStatus = etmStatus
                self.sigETMStatusChanged.emit(etmStatus)
            time.sleep(1)

    @pyqtSlot()
    def slotStartETM(self):
        sd = self.prepareSocket()
        sd.sendall(b"ETM_START\0")
        sd.close()
        if self.window.settings.getint("xwared", "startetmwhen") == 2:
            self.window.settings.setbool("xwared", "startetm", True)
            self.window.settings.save()

    @pyqtSlot()
    def slotStopETM(self):
        sd = self.prepareSocket()
        sd.sendall(b"ETM_STOP\0")
        sd.close()
        if self.window.settings.getint("xwared", "startetmwhen") == 2:
            self.window.settings.setbool("xwared", "startetm", False)
            self.window.settings.save()

    @pyqtSlot()
    def slotRestartETM(self):
        sd = self.prepareSocket()
        sd.sendall(b"ETM_RESTART\0")
        sd.close()
        if self.window.settings.getint("xwared", "startetmwhen") == 2:
            self.window.settings.setbool("xwared", "startetm", True)
            self.window.settings.save()

    @staticmethod
    def prepareSocket():
        import socket

        sd = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM, 0)
        sd.connect(constants.XWARED_SOCKET)
        return sd