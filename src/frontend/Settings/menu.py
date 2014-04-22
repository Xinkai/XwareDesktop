# -*- coding: utf-8 -*-

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QMenu


class SettingMenu(QMenu):
    # A QMenu that allows settings to be done.
    def __init__(self, parent):
        super().__init__(parent)
        self.aboutToShow.connect(self.slotLoadSettings)
        self.aboutToHide.connect(self.slotSaveSettings)

    @pyqtSlot()
    def slotLoadSettings(self):
        for action in self.actions():
            if hasattr(action, "defaultWidget"):
                action.defaultWidget().loadSetting()

    @pyqtSlot()
    def slotSaveSettings(self):
        for action in self.actions():
            if hasattr(action, "defaultWidget"):
                action.defaultWidget().saveSetting()
