# -*- coding: utf-8 -*-

import logging

import os, threading
import pickle, binascii
from utils.system import runAsIndependentProcess


class CrashReport(object):
    def __init__(self, tb):
        super().__init__()
        payload = dict(traceback = tb,
                       thread = threading.current_thread().name)

        crappFile = os.path.join(os.path.dirname(__file__), "CrashReportApp.py")
        crappArgs = self.encodePayload(payload)
        runAsIndependentProcess(crappFile + " " + crappArgs)

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
