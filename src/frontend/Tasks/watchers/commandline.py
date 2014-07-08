# -*- coding: utf-8 -*-

import logging

from PyQt5.QtCore import QObject
from multiprocessing.connection import Listener, Client

import threading

import constants
from utils.misc import tryRemove


class CommandlineClient(object):
    def __init__(self, payload):
        with Client(*constants.FRONTEND_SOCKET) as conn:
            conn.send(payload)


class CommandlineWatcher(QObject):
    def __init__(self, parent):
        super().__init__(parent)
        self.agent = parent
        self._listener = threading.Thread(target = self.listenerThread, daemon = True,
                                          name = "frontend communication listener")
        self._listener.start()

    def listenerThread(self):
        # clean if previous run crashes
        tryRemove(constants.FRONTEND_SOCKET[0])

        with Listener(*constants.FRONTEND_SOCKET) as listener:
            while True:
                with listener.accept() as conn:
                    payload = conn.recv()
                    self.agent.createTasksAction(payload)
