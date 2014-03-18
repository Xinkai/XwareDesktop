# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QGraphicsView

class MonitorGraphicsView(QGraphicsView):
    monitorWin = None
    def __init__(self, parent = None):
        super().__init__(parent)
        self.monitorWin = parent

    def mousePressEvent(self, qMouseEvent):
        self.monitorWin.mousePressEvent(qMouseEvent)

    def mouseMoveEvent(self, qMouseEvent):
        self.monitorWin.mouseMoveEvent(qMouseEvent)

    def mouseReleaseEvent(self, qMouseEvent):
        self.monitorWin.mouseReleaseEvent(qMouseEvent)
