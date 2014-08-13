# -*- coding: utf-8 -*-

import logging
from launcher import app

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QWidget, QWidgetAction

from legacy.CustomStatusBar.CStatusButton import CustomStatusBarToolButton
from .ui_quickspeedlimit import Ui_Form_quickSpeedLimit
from .menu import SettingMenu


class QuickSpeedLimitBtn(CustomStatusBarToolButton):
    def __init__(self, parent):
        super().__init__(parent)
        menu = SettingMenu(self)
        action = SpeedLimitingWidgetAction(self)
        menu.addAction(action)
        self.setMenu(menu)
        self.setText("限速")

        # Should be disabled when ETM not running
        app.adapterManager[0].infoUpdated.connect(self.slotXwareStatusChanged)
        self.slotXwareStatusChanged()

    @pyqtSlot()
    def slotXwareStatusChanged(self):
        self.setEnabled(app.adapterManager[0].etmPid != 0)


class SpeedLimitingWidgetAction(QWidgetAction):
    def __init__(self, parent):
        super().__init__(parent)
        widget = QuickSpeedLimitForm(parent)
        self.setDefaultWidget(widget)


class QuickSpeedLimitForm(QWidget, Ui_Form_quickSpeedLimit):
    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)
        self.checkBox_ulSpeedLimit.stateChanged.connect(self.slotStateChanged)
        self.checkBox_dlSpeedLimit.stateChanged.connect(self.slotStateChanged)
        self.slotStateChanged()

    def slotStateChanged(self):
        self.spinBox_ulSpeedLimit.setEnabled(self.checkBox_ulSpeedLimit.isChecked())
        self.spinBox_dlSpeedLimit.setEnabled(self.checkBox_dlSpeedLimit.isChecked())

    def loadSetting(self):
        adapter = app.adapterManager[0]
        settings = adapter.backendSettings
        self.setEnabled(adapter.etmPid != 0 and settings.initialized)
        if not self.isEnabled():
            return

        if settings.downloadSpeedLimit == -1:
            self.checkBox_dlSpeedLimit.setChecked(False)
            self.spinBox_dlSpeedLimit.setValue(
                app.settings.getint("adapter-legacy", "dlspeedlimit"))
        else:
            self.checkBox_dlSpeedLimit.setChecked(True)
            self.spinBox_dlSpeedLimit.setValue(settings.downloadSpeedLimit)

        if settings.uploadSpeedLimit == -1:
            self.checkBox_ulSpeedLimit.setChecked(False)
            self.spinBox_ulSpeedLimit.setValue(
                app.settings.getint("adapter-legacy", "ulspeedlimit"))
        else:
            self.checkBox_ulSpeedLimit.setChecked(True)
            self.spinBox_ulSpeedLimit.setValue(settings.uploadSpeedLimit)

    def saveSetting(self):
        if not self.isEnabled():
            return

        adapter = app.adapterManager[0]

        # called by parent menu's saveSettings.
        if self.checkBox_ulSpeedLimit.isChecked():
            ulSpeedLimit = self.spinBox_ulSpeedLimit.value()
        else:
            ulSpeedLimit = -1

        if self.checkBox_dlSpeedLimit.isChecked():
            dlSpeedLimit = self.spinBox_dlSpeedLimit.value()
        else:
            dlSpeedLimit = -1

        adapter.do_applySettings({
            "downloadSpeedLimit": dlSpeedLimit,
            "uploadSpeedLimit": ulSpeedLimit,
        })
