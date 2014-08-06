# -*- coding: utf-8 -*-

import logging

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction

from launcher import app
from Settings.menu import SettingMenu
from Settings.QuickSpeedLimit import SpeedLimitingWidgetAction


class ToggleMonitorWinAction(QAction):
    def __init__(self, parent):
        super().__init__(parent)
        self.setText("显示悬浮窗")
        self.setCheckable(True)
        self.triggered[bool].connect(self.settingToggled)

    def defaultWidget(self):
        # Fake a custom actionwidget
        # see Settings.menu for more information
        return self

    def loadSetting(self):
        self.setChecked(app.settings.getbool("frontend", "showmonitorwindow"))

    def saveSetting(self):
        pass
        # handled by self.settingToggled

    @pyqtSlot(bool)
    def settingToggled(self, checked):
        app.settings.setbool("frontend", "showmonitorwindow", checked)
        app.settings.applySettings.emit()


class ExitAppAction(QAction):
    def __init__(self, parent):
        super().__init__(parent)
        self.setText("退出")
        self.setIcon(QIcon.fromTheme("application-exit"))
        self.triggered.connect(app.quit)


class ContextMenu(SettingMenu):
    def __init__(self, parent):
        super().__init__(parent)

        self._speedLimitAction = SpeedLimitingWidgetAction(self)
        self.addAction(self._speedLimitAction)

        self._toggleMonitorWinAction = ToggleMonitorWinAction(self)
        self.addAction(self._toggleMonitorWinAction)

        self._exitAppAction = ExitAppAction(self)
        self.addAction(self._exitAppAction)
