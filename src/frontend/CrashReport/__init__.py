# -*- coding: utf-8 -*-

import logging

import os, threading, sys
import pickle, binascii
from utils.system import runAsIndependentProcess


class CrashReport(object):
    def __init__(self, tb):
        super().__init__()
        payload = dict(traceback = tb,
                       thread = threading.current_thread().name)

        interpreter = sys.executable  # crashreport app is run by the same implementation
        crappFile = os.path.join(os.path.dirname(__file__), "CrashReportApp.py")
        crappArgs = self.encodePayload(payload)
        runAsIndependentProcess([interpreter, crappFile, crappArgs])

    @staticmethod
    def encodePayload(payload):
        pickled = pickle.dumps(payload, pickle.HIGHEST_PROTOCOL)
        pickledBytes = binascii.hexlify(pickled)
        pickledStr = pickledBytes.decode("ascii")
        return pickledStr

    @staticmethod
    def decodePayload(payload):
        pickledBytes = payload.encode("ascii")
        pickled = binascii.unhexlify(pickledBytes)
        unpickled = pickle.loads(pickled)
        return unpickled
