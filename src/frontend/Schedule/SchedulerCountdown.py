# -*- coding: utf-8 -*-

import logging
from launcher import app

from PyQt5.QtCore import QTimer, Qt, pyqtSlot
from PyQt5.QtWidgets import QMessageBox


class CountdownMessageBox(QMessageBox):
    def __init__(self, action, model):
        self._actionDisplayName = str(action)
        self._model = model
        super().__init__(QMessageBox.Question,  # icon
                         "Xware Desktop任务完成",     # title
                         "",
                         QMessageBox.NoButton,  # buttons
                         getattr(app, "mainWin", None),  # parent
                         Qt.Dialog | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_DeleteOnClose)
        # Note: setting WindowModality cancels StaysOnTop
        # self.setWindowModality(Qt.ApplicationModal)

        # Due to a possible Qt Bug, the reject button must be added first.
        # https://bugreports.qt-project.org/browse/QTBUG-37870
        self.rejectBtn = self.addButton("取消", QMessageBox.RejectRole)
        self.acceptBtn = self.addButton("立刻执行", QMessageBox.AcceptRole)

        self._timeout = 60
        self.updateText()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.slotTick)
        self._timer.start(1000)  # one tick per second

    @pyqtSlot()
    def slotTick(self):
        if self._timeout > 0:
            self.updateText()
            self._timeout -= 1
        else:
            self.accept()

    def updateText(self):
        self.setText("任务已完成。将于{}秒后{}。".format(self._timeout, self._actionDisplayName))

    def done(self, result: int):
        if result == QMessageBox.Accepted:
            self._model.countdownConfirmed.emit(True)
        elif result == QMessageBox.Rejected:
            self._model.countdownConfirmed.emit(False)
        else:
            raise ValueError("Unknown result: {}".format(result))
        return super().done(result)
