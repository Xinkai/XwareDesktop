# -*- coding: utf-8 -*-

from PyQt5.QtCore import QObject
import requests
import collections

EtmSetting = collections.namedtuple("EtmSetting", ["dLimit", "uLimit", "maxRunningTasksNum"])

class EtmPy(QObject):
    def __init__(self, mainWin):
        super().__init__(mainWin)
        self.mainWin = mainWin
        self.rcport = 9000

    @property
    def rcontrol(self):
        return "http://127.0.0.1:{0}/".format(self.rcport)

    def getSettings(self):
        req = requests.get(self.rcontrol + "getspeedlimit")
        limits = req.json()[1:] # not sure about what first element means, ignore for now

        req = requests.get(self.rcontrol + "getrunningtaskslimit")
        maxRunningTasksNum = req.json()[1]

        return EtmSetting(dLimit = limits[0], uLimit = limits[1],
                          maxRunningTasksNum = maxRunningTasksNum)

    def saveSettings(self, newsettings):
        requests.post(self.rcontrol + \
                      "settings?downloadSpeedLimit={}&uploadSpeedLimit={}&maxRunTaskNumber={}".format(*newsettings))

