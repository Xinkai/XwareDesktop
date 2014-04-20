# -*- coding: utf-8 -*-

import logging

import os, threading
import pickle, binascii


class CrashReport(object):
    def __init__(self, tb):
        super().__init__()
        payload = dict(traceback = tb,
                       thread = threading.current_thread().name)
        pid = os.fork()
        if pid == 0:
            # child
            cmd = (os.path.join(os.path.dirname(__file__), "CrashReportApp.py"),
                   self.encodePayload(payload))
            os.execv(cmd[0], cmd)
        else:
            pass

    @staticmethod
    def encodePayload(payload):
        pickled = pickle.dumps(payload, 3)  # protocol 3 requires Py3.0
        pickledBytes = binascii.hexlify(pickled)
        pickledStr = pickledBytes.decode("ascii")
        return pickledStr

    @staticmethod
    def decodePayload(payload):
        pickledBytes = payload.encode("ascii")
        pickled = binascii.unhexlify(pickledBytes)
        unpickled = pickle.loads(pickled)
        return unpickled
