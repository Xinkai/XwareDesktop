# -*- coding: utf-8 -*-

import logging
from launcher import app

from PyQt5.QtCore import pyqtSignal, QObject
from shared.config import SettingsAccessorBase


class SettingsAccessor(QObject, SettingsAccessorBase):
    applySettings = pyqtSignal()

    def __init__(self, parent, configFilePath, defaultDict):
        super().__init__(QObject_parent = parent,
                         configFilePath = configFilePath,
                         defaultDict = defaultDict)
        app.aboutToQuit.connect(self.save)
