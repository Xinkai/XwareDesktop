# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QApplication

from Compat.TeardownHelper import TeardownHelper


class MonitorWidget(QWidget, TeardownHelper):
    _isBeingDragged = False
    _dragOffset = None

    app = None

    def __init__(self, parent = None):
        super().__init__(parent)
        self.app = QApplication.instance()
        self.setWindowFlags(Qt.FramelessWindowHint |
                            Qt.ToolTip |
                            Qt.WindowStaysOnTopHint)

    def mousePressEvent(self, qMouseEvent):
        self._isBeingDragged = True
        self._dragOffset = qMouseEvent.pos()

    def mouseMoveEvent(self, qMouseEvent):
        if self._isBeingDragged:
            self.move(qMouseEvent.globalPos() - self._dragOffset)

    def mouseReleaseEvent(self, qMouseEvent):
        if qMouseEvent.button() == Qt.LeftButton:
            self._isBeingDragged = False
            self._dragOffset = None

    def mouseDoubleClickEvent(self, qMouseEvent):
        self.app.mainWin.restore()
