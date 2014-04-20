# -*- coding: utf-8 -*-

import logging

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
import threading, time
import fcntl
import constants


# an interface to watch, notify, and supervise the status of xwared and ETM
class XwaredPy(QObject):
    sigXwaredStatusPolled = pyqtSignal(bool)
    sigETMStatusPolled = pyqtSignal()

    etmStatus = None
    xwaredStatus = None

    _t = None

    def __init__(self, app):
        super().__init__(app)
        self.app = app

        self.app.aboutToQuit.connect(self.stopXware)
        self.startXware()
        self._t = threading.Thread(target = self._watcherThread, daemon = True,
                                   name = "xwared/etm watch thread")
        self._t.start()
        self.app.sigMainWinLoaded.connect(self.connectUI)

    @pyqtSlot()
    def connectUI(self):
        # Note: The menu actions enable/disable toggling are handled by statusbar.
        self.app.mainWin.action_ETMstart.triggered.connect(self.slotStartETM)
        self.app.mainWin.action_ETMstop.triggered.connect(self.slotStopETM)
        self.app.mainWin.action_ETMrestart.triggered.connect(self.slotRestartETM)

    def startXware(self):
        if self.app.settings.getint("xwared", "startetmwhen") == 3:
            self.slotStartETM()
            self.app.settings.setbool("xwared", "startetm", True)
            self.app.settings.save()

    def stopXware(self):
        if self.app.settings.getint("xwared", "startetmwhen") == 3:
            self.slotStopETM()
            self.app.settings.setbool("xwared", "startetm", True)
            self.app.settings.save()

    def _watcherThread(self):
        while True:
            try:
                xwaredLockFile = open(constants.XWARED_LOCK)
                try:
                    fcntl.flock(xwaredLockFile, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    self.xwaredStatus = False
                    fcntl.flock(xwaredLockFile, fcntl.LOCK_UN)
                except BlockingIOError:
                    self.xwaredStatus = True
                xwaredLockFile.close()
            except FileNotFoundError:
                self.xwaredStatus = False

            self.sigXwaredStatusPolled.emit(self.xwaredStatus)

            try:
                etmLockFile = open(constants.ETM_LOCK)
                try:
                    fcntl.flock(etmLockFile, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    self.etmStatus = False
                    fcntl.flock(etmLockFile, fcntl.LOCK_UN)
                except BlockingIOError:
                    self.etmStatus = True
                etmLockFile.close()
            except FileNotFoundError:
                self.etmStatus = False

            self.sigETMStatusPolled.emit()
            time.sleep(1)

    @pyqtSlot()
    def slotStartETM(self):
        sd = self.__prepareSocket()
        if sd:
            sd.sendall(b"ETM_START\0")
            sd.close()
        if self.app.settings.getint("xwared", "startetmwhen") == 2:
            self.app.settings.setbool("xwared", "startetm", True)
            self.app.settings.save()

    @pyqtSlot()
    def slotStopETM(self):
        sd = self.__prepareSocket()
        if sd:
            sd.sendall(b"ETM_STOP\0")
            sd.close()
        if self.app.settings.getint("xwared", "startetmwhen") == 2:
            self.app.settings.setbool("xwared", "startetm", False)
            self.app.settings.save()

    @pyqtSlot()
    def slotRestartETM(self):
        sd = self.__prepareSocket()
        if sd:
            sd.sendall(b"ETM_RESTART\0")
            sd.close()
        if self.app.settings.getint("xwared", "startetmwhen") == 2:
            self.app.settings.setbool("xwared", "startetm", True)
            self.app.settings.save()

    @staticmethod
    def __prepareSocket():
        import socket

        sd = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM, 0)
        try:
            sd.connect(constants.XWARED_SOCKET)
            return sd
        except FileNotFoundError:
            logging.error("XWARED_SOCKET doesn't exist, check if xwared is running.")
            return None
