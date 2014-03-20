# -*- coding: utf-8 -*-

from PyQt5.Qt import Qt
from PyQt5.QtWidgets import QWidget

class MonitorWidget(QWidget):
    _isBeingDragged = False
    _dragOffset = None

    def __init__(self, parent = None):
        super().__init__(parent)
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
