# -*- coding: utf-8 -*-

import logging
from launcher import app

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QIcon

from .SchedulerWin import SchedulerWindow
from .CustomStatusBar.CStatusButton import CustomStatusBarButton


class SchedulerButton(CustomStatusBarButton):
    def __init__(self, parent):
        super().__init__(parent)
        self.setIcon(QIcon.fromTheme("clock"))
        self.updateText()
        app.schedulerModel.schedulerSummaryChanged.connect(self.updateText)
        self.clicked.connect(self.slotClicked)

    @pyqtSlot()
    def slotClicked(self):
        app.mainWin.schedulerWin = SchedulerWindow(app.mainWin)
        app.mainWin.schedulerWin.show()

    def updateText(self):
        blockingCount = app.schedulerModel.blockingTaskCount
        action = app.schedulerModel.action
        if not action:
            self.setText("计划任务")
            return
        if blockingCount:
            self.setText("{count}个任务结束后{action}"
                         .format(count = blockingCount,
                                 action = str(action)))
        else:
            self.setText("计划任务")
