# -*- coding: utf-8 -*-

import logging
from launcher import app

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

import threading, time
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


class SocketDoesntExist(FileNotFoundError):
    pass


def callXwaredInterface(funcName, *args, **kwargs):
    try:
        client = _XwaredCommunicationClient()
    except FileNotFoundError as e:
        raise SocketDoesntExist(e)

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
    sigXwaredStatusPolled = pyqtSignal(bool)
    sigETMStatusPolled = pyqtSignal()

    etmStatus = None
    xwaredStatus = None
    userId = None
    peerId = None
    lcPort = None

    _t = None

    def __init__(self, parent):
        super().__init__(parent)

        app.aboutToQuit.connect(self.stopXware)
        self.startXware()
        self._t = threading.Thread(target = self._watcherThread, daemon = True,
                                   name = "xwared/etm watch thread")
        self._t.start()
        app.sigMainWinLoaded.connect(self.connectUI)

    @pyqtSlot()
    def connectUI(self):
        # Note: The menu actions enable/disable toggling are handled by statusbar.
        app.mainWin.action_ETMstart.triggered.connect(self.slotStartETM)
        app.mainWin.action_ETMstop.triggered.connect(self.slotStopETM)
        app.mainWin.action_ETMrestart.triggered.connect(self.slotRestartETM)

    @staticmethod
    def startXware():
        try:
            callXwaredInterface("start")  # TODO: when remote, disable this
        except SocketDoesntExist:
            pass

    @staticmethod
    def stopXware():
        try:
            callXwaredInterface("quit")  # TODO: when remote, disable this
        except SocketDoesntExist:
            pass

    def _watcherThread(self):
        while True:
            try:
                backendInfo = callXwaredInterface("infoPoll")
                self.xwaredStatus = True
                self.etmStatus = True if backendInfo.etmPid else False
                self.lcPort = backendInfo.lcPort
                self.userId = backendInfo.userId
                self.peerId = backendInfo.peerId
            except SocketDoesntExist:
                self.xwaredStatus = False
                self.etmStatus = False
                self.lcPort = 0
                self.userId = 0
                self.peerId = ""

            self.sigXwaredStatusPolled.emit(self.xwaredStatus)
            self.sigETMStatusPolled.emit()
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
        raise NotImplementedError

    @managedBySystemd.setter
    def managedBySystemd(self, on):
        raise NotImplementedError

    @property
    def managedByUpstart(self):
        raise NotImplementedError

    @managedByUpstart.setter
    def managedByUpstart(self, on):
        raise NotImplementedError

    @property
    def managedByAutostart(self):
        raise NotImplementedError

    @managedByAutostart.setter
    def managedByAutostart(self, on):
        raise NotImplementedError
