# -*- coding: utf-8 -*-

from PyQt5.QtCore import QObject
from .model import Action


class Win32PowerActionManager(QObject):
    def __init__(self, parent):
        super().__init__(parent)
        self.actions = [Action.Null]

    def act(self, action):
        raise NotImplementedError("Cannot do {}".format(action))
