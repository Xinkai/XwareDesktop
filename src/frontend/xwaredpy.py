# -*- coding: utf-8 -*-

import logging
from launcher import app

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, pyqtProperty

import threading, time
import os
from utils.misc import tryRemove, trySymlink, tryMkdir
from utils.system import getInitType, InitType
import constants

from multiprocessing.connection import Client


class _XwaredCommunicationClient(object):
    funcName = None
    args = tuple()
    kwargs = dict()
    sent = False
    conn = None
    response = None
    received = False

    def __init__(self):
        self.conn = Client(*constants.XWARED_SOCKET)

    def send(self):
        if not self.funcName:
            raise ValueError("no funcName")
        self.conn.send([self.funcName, self.args, self.kwargs])
        self.sent = True
        self.response = self.conn.recv()
        self.received = True
        self.conn.close()

    def setFunc(self, funcName):
        if self.sent:
            raise Exception("sent already.")
        self.funcName = funcName

    def setArgs(self, args):
        if self.sent:
            raise Exception("sent already.")
        self.args = args

    def setKwargs(self, kwargs):
        if self.sent:
            raise Exception("sent already.")
        self.kwargs = kwargs

    def getReturnValue(self):
        if not self.sent:
            raise Exception("not sent yet.")
        if not self.received:
            raise Exception("not received yet.")
        return self.response


class InvalidSocket(FileNotFoundError, ConnectionRefusedError):
    pass


def callXwaredInterface(funcName, *args, **kwargs):
    try:
        client = _XwaredCommunicationClient()
    except (FileNotFoundError, ConnectionRefusedError) as e:
        logging.error("XwaredInterface InvalidSocket with method {}".format(funcName))
        raise InvalidSocket(e)

    client.setFunc(funcName)
    if args:
        client.setArgs(args)
    if kwargs:
        client.setKwargs(kwargs)
    client.send()
    result = client.getReturnValue()
    logging.info("{funcName} -> {result}".format(**locals()))
    del client
    return result


# an interface to watch, notify, and supervise the status of xwared and ETM
class XwaredPy(QObject):
    statusUpdated = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self._etmStatus = None
        self._xwaredStatus = None
        self._userId = None
        self._peerId = None
        self._lcPort = None

        app.aboutToQuit.connect(self.stopXware)
        self.startXware()
        self._thread = threading.Thread(target = self._watcherThread,
                                        daemon = True,
                                        name = "xwared/etm watch thread")
        self._thread.start()
        app.sigMainWinLoaded.connect(self.connectUI)

    @pyqtProperty(bool, notify = statusUpdated)
    def etmStatus(self):
        return self._etmStatus

    @pyqtProperty(bool, notify = statusUpdated)
    def xwaredStatus(self):
        return self._xwaredStatus

    @pyqtProperty(str, notify = statusUpdated)
    def userId(self):
        import warnings
        warnings.warn("XwareClient getsysinfo can do this", DeprecationWarning)
        return self._userId

    @pyqtProperty(str, notify = statusUpdated)
    def peerId(self):
        return self._peerId

    @pyqtProperty(int, notify = statusUpdated)
    def lcPort(self):
        return self._lcPort

    def _statusUpdate(self, etmStatus, xwaredStatus, userId, peerId, lcPort):
        self._etmStatus = etmStatus
        self._xwaredStatus = xwaredStatus
        self._userId = userId
        self._peerId = peerId
        self._lcPort = lcPort
        self.statusUpdated.emit()

    @pyqtSlot()
    def connectUI(self):
        # Note: The menu actions enable/disable toggling are handled by statusbar.
        app.mainWin.action_ETMstart.triggered.connect(self.slotStartETM)
        app.mainWin.action_ETMstop.triggered.connect(self.slotStopETM)
        app.mainWin.action_ETMrestart.triggered.connect(self.slotRestartETM)

    @staticmethod
    def startXware():
        try:
            callXwaredInterface("start")
        except InvalidSocket:
            pass

    @staticmethod
    def stopXware():
        try:
            callXwaredInterface("quit")
        except InvalidSocket:
            pass

    @property
    def startEtmWhen(self):
        # return None if cannot get the value
        try:
            return callXwaredInterface("getStartEtmWhen")
        except InvalidSocket:
            return None

    @startEtmWhen.setter
    def startEtmWhen(self, value):
        callXwaredInterface("setStartEtmWhen", value)

    def _watcherThread(self):
        while True:
            try:
                backendInfo = callXwaredInterface("infoPoll")
                self._statusUpdate(etmStatus = True if backendInfo.etmPid else False,
                                   xwaredStatus = True,
                                   userId = backendInfo.userId,
                                   peerId = backendInfo.peerId,
                                   lcPort = backendInfo.lcPort)
            except InvalidSocket:
                self._statusUpdate(etmStatus = False,
                                   xwaredStatus = False,
                                   userId = 0,
                                   peerId = "",
                                   lcPort = 0)

            time.sleep(1)

    @pyqtSlot()
    def slotStartETM(self):
        callXwaredInterface("startETM")

    @pyqtSlot()
    def slotStopETM(self):
        callXwaredInterface("stopETM")

    @pyqtSlot()
    def slotRestartETM(self):
        callXwaredInterface("restartETM")

    @property
    def managedBySystemd(self):
        return os.path.lexists(constants.SYSTEMD_SERVICE_ENABLED_USERFILE) and \
            os.path.lexists(constants.SYSTEMD_SERVICE_USERFILE)

    @managedBySystemd.setter
    def managedBySystemd(self, on):
        if on:
            tryMkdir(os.path.dirname(constants.SYSTEMD_SERVICE_ENABLED_USERFILE))

            trySymlink(constants.SYSTEMD_SERVICE_FILE,
                       constants.SYSTEMD_SERVICE_USERFILE)

            trySymlink(constants.SYSTEMD_SERVICE_USERFILE,
                       constants.SYSTEMD_SERVICE_ENABLED_USERFILE)
        else:
            tryRemove(constants.SYSTEMD_SERVICE_ENABLED_USERFILE)
            tryRemove(constants.SYSTEMD_SERVICE_USERFILE)
        if getInitType() == InitType.SYSTEMD:
            os.system("systemctl --user daemon-reload")

    @property
    def managedByUpstart(self):
        return os.path.lexists(constants.UPSTART_SERVICE_USERFILE)

    @managedByUpstart.setter
    def managedByUpstart(self, on):
        if on:
            tryMkdir(os.path.dirname(constants.UPSTART_SERVICE_USERFILE))

            trySymlink(constants.UPSTART_SERVICE_FILE,
                       constants.UPSTART_SERVICE_USERFILE)
        else:
            tryRemove(constants.UPSTART_SERVICE_USERFILE)
        if getInitType() == InitType.UPSTART:
            os.system("initctl --user reload-configuration")

    @property
    def managedByAutostart(self):
        return os.path.lexists(constants.AUTOSTART_DESKTOP_USERFILE)

    @managedByAutostart.setter
    def managedByAutostart(self, on):
        if on:
            tryMkdir(os.path.dirname(constants.AUTOSTART_DESKTOP_USERFILE))

            trySymlink(constants.AUTOSTART_DESKTOP_FILE,
                       constants.AUTOSTART_DESKTOP_USERFILE)
        else:
            tryRemove(constants.AUTOSTART_DESKTOP_USERFILE)
