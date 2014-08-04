# -*- coding: utf-8 -*-

import logging
from launcher import app

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QWidget, QWidgetAction

from etmpy import EtmSetting
from legacy.CustomStatusBar.CStatusButton import CustomStatusBarToolButton
from legacy.ui_quickspeedlimit import Ui_Form_quickSpeedLimit
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
        etmSettings = app.etmpy.getSettings()

        self.setEnabled(bool(etmSettings))
        if not self.isEnabled():
            return

        if etmSettings.dLimit == -1:
            self.checkBox_dlSpeedLimit.setChecked(False)
            self.spinBox_dlSpeedLimit.setValue(app.settings.getint("internal", "dlspeedlimit"))
        else:
            self.checkBox_dlSpeedLimit.setChecked(True)
            self.spinBox_dlSpeedLimit.setValue(etmSettings.dLimit)

        if etmSettings.uLimit == -1:
            self.checkBox_ulSpeedLimit.setChecked(False)
            self.spinBox_ulSpeedLimit.setValue(app.settings.getint("internal", "ulspeedlimit"))
        else:
            self.checkBox_ulSpeedLimit.setChecked(True)
            self.spinBox_ulSpeedLimit.setValue(etmSettings.uLimit)

    def saveSetting(self):
        if not self.isEnabled():
            return

        # called by parent menu's saveSettings.
        if self.checkBox_ulSpeedLimit.isChecked():
            ulSpeedLimit = self.spinBox_ulSpeedLimit.value()
        else:
            ulSpeedLimit = -1

        if self.checkBox_dlSpeedLimit.isChecked():
            dlSpeedLimit = self.spinBox_dlSpeedLimit.value()
        else:
            dlSpeedLimit = -1

        newEtmSetting = EtmSetting(dLimit = dlSpeedLimit, uLimit = ulSpeedLimit,
                                   maxRunningTasksNum = None)
        app.etmpy.saveSettings(newEtmSetting)
