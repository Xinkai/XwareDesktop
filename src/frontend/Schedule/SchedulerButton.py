# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QIcon

from Schedule.SchedulerWin import SchedulerWindow
from CustomStatusBar.CStatusButton import CustomStatusBarButton


class SchedulerButton(CustomStatusBarButton):
    def __init__(self, parent):
        super().__init__(parent)
        self.setIcon(QIcon(":/image/clock.png"))
        self.updateText()
        self.app.scheduler.sigSchedulerSummaryUpdated.connect(self.updateText)
        self.clicked.connect(self.slotClicked)

    @pyqtSlot()
    def slotClicked(self):
        mainWin = self.app.mainWin
        mainWin.schedulerWin = SchedulerWindow(mainWin)
        mainWin.schedulerWin.show()

    def updateText(self):
        summary = self.app.scheduler.getSummary()
        if type(summary) is str:
            self.setText(summary)
        else:
            # True / False
            self.setText("计划任务")
