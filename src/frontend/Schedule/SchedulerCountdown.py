# -*- coding: utf-8 -*-

import logging

from PyQt5.QtCore import QTimer, Qt, pyqtSlot
from PyQt5.QtWidgets import QMessageBox, QApplication

class CountdownMessageBox(QMessageBox):
    app = None
    _timeout = None
    _timer = None
    _actionStr = None
    def __init__(self, actionStr):
        self.app = QApplication.instance()
        self._actionStr = actionStr
        super().__init__(QMessageBox.Question, # icon
                         "Xware Desktop任务完成",     # title
                         "",
                         QMessageBox.NoButton, # buttons
                         getattr(self.app, "mainWin", None), # parent
                         Qt.Dialog | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowModality(Qt.ApplicationModal)

        # Due to a possible Qt Bug, the reject button must be added first.
        # https://bugreports.qt-project.org/browse/QTBUG-37870
        self.rejectBtn = self.addButton("取消", QMessageBox.RejectRole)
        self.acceptBtn = self.addButton("立刻执行", QMessageBox.AcceptRole)

        self.accepted.connect(self.act)
        self.rejected.connect(self.reset)

        self._timeout = 60
        self.updateText()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.slotTick)
        self._timer.start(1000) # one tick per second

    @pyqtSlot()
    def slotTick(self):
        print("Scheduler countdown tick...", self._timeout)
        if self._timeout > 0:
            self._timeout -= 1
            self.updateText()
        else:
            self.accept()

    def updateText(self):
        self.setText("任务已完成。将于{}秒后{}。".format(self._timeout,
                                                      self._actionStr))
    @pyqtSlot()
    def act(self):
        print("Scheduler confirmation accepted")
        self.app.scheduler.sigActionConfirmed.emit(True)
        self.close()

    @pyqtSlot()
    def reset(self):
        print("Scheduler confirmation rejected")
        self.app.scheduler.sigActionConfirmed.emit(False)
        self.close()
