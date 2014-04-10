# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QComboBox


class CompatComboBox(QComboBox):
    def __init__(self, parent):
        super().__init__(parent)
        if not hasattr(self, "currentData"):
            self.currentData = self._currentData

    def _currentData(self):
        # introduced in Qt 5.2
        return self.itemData(self.currentIndex())
