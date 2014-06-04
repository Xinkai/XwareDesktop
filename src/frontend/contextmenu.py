# -*- coding: utf-8 -*-

import logging

from launcher import app
from Settings.menu import SettingMenu
from Settings.QuickSpeedLimit import SpeedLimitingWidgetAction


class ContextMenu(SettingMenu):
    def __init__(self, parent):
        super().__init__(parent)

        self._speedLimitAction = SpeedLimitingWidgetAction(self)
        self.addAction(self._speedLimitAction)

        self.addAction(app.mainWin.action_exit)
