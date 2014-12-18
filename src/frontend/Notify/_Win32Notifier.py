# -*- coding: utf-8 -*-

from PyQt5.QtCore import QObject


class Win32Notifier(QObject):
    def __init__(self, *, taskModel, frontendSettings, parent):
        super().__init__(parent)
