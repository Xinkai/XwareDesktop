# -*- coding: utf-8 -*-

import socket
import constants

class DaemonCommunication(object):
    def __init__(self):
        self.sd = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM, 0)
        self.sd.connect(constants.DAEMON_SOCKET)

    def stopETM(self):
        self.sd.sendall(b"ETM_STOP\0")

    def startETM(self):
        self.sd.sendall(b"ETM_START\0")

    def restartETM(self):
        self.sd.sendall(b"ETM_RESTART\0")

import threading
from multiprocessing.connection import Listener, Client

class FrontendCommunicationListener(object):
    def __init__(self, window):
        self.window = window
        t = threading.Thread(target = self.startListenerThread, daemon = True)
        t.start()

    def startListenerThread(self):
        with Listener(*constants.FRONTEND_SOCKET) as listener:
            while True:
                with listener.accept() as conn:
                    result = conn.recv()
                    self.window.emit(self.window.action_createTask)
                    print("payload", result)

class FrontendCommunicationClient(object):
    def __init__(self, payload):
        with Client(*constants.FRONTEND_SOCKET) as conn:
            conn.send(payload)

