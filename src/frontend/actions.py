# -*- coding: utf-8 -*-

from PyQt5.QtCore import QObject

from collections import deque
import threading, os

from multiprocessing.connection import Listener, Client

import constants

class FrontendAction(object):
    def __init__(self):
        super().__init__()

class NewTaskAction(FrontendAction):
    def __init__(self, *args, **kwargs):
        super().__init__()

    def prepareOneLink(self, link):
        # TODO: private link
        return link

class NewTorrentTaskAction(NewTaskAction):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class FrontendActionsQueue(QObject):
    _queue = None
    _listener = None
    frontendpy = None

    def __init__(self, parent = None):
        super().__init__(parent)
        self._queue = deque()
        self.frontendpy = parent

        self._listener = threading.Thread(target = self.listenerThread, daemon = True,
                                          name = "frontend communication listener")
        self._listener.start()

    def listenerThread(self):
        # clean if previous run crashes
        try:
            os.remove(constants.FRONTEND_SOCKET[0])
        except FileNotFoundError:
            pass

        with Listener(*constants.FRONTEND_SOCKET) as listener:
            while True:
                with listener.accept() as conn:
                    payload = conn.recv()
                    self.frontendpy.slotPrepareTasksCreation(payload)
                    print("payload", payload)

class FrontendCommunicationClient(object):
    def __init__(self, payload):
        with Client(*constants.FRONTEND_SOCKET) as conn:
            conn.send(payload)