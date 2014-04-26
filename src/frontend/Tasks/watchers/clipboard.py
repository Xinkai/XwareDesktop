# -*- coding: utf-8 -*-

from launcher import app

from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.QtWidgets import QApplication


class ClipboardWatcher(QObject):
    def __init__(self, parent):
        super().__init__(parent)
        self.agent = parent
        self._clipboard = QApplication.clipboard()
        app.settings.applySettings.connect(self.slotWatchClipboardToggled)

    @pyqtSlot()
    def slotWatchClipboardToggled(self):
        try:
            self._clipboard.dataChanged.disconnect(self.slotClipboardDataChanged)
        except TypeError:
            pass  # not connected, meaning settings says no watch clipboard
        on = app.settings.getbool("frontend", "watchclipboard")
        if on:
            self._clipboard.dataChanged.connect(self.slotClipboardDataChanged)

    @pyqtSlot()
    def slotClipboardDataChanged(self):
        mimeData = self._clipboard.mimeData()
        self.agent.createTasksFromMimeData(mimeData)
