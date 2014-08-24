# -*- coding: utf-8 -*-

import logging
from launcher import app

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget


class MonitorWidget(QWidget):
    def __init__(self, parent = None):
        super().__init__(parent)
        # self.setAttribute(Qt.WA_X11NetWmWindowTypeDock, True)
        # self.setAttribute(Qt.WA_X11NetWmWindowTypeSplash, True)



        self._isBeingDragged = False
        self._dragOffset = None
        self.setWindowFlags(Qt.FramelessWindowHint
                            # Qt.Dialog |
                            # Qt.ToolTip |
                            # Qt.Tool |
                            | Qt.WindowStaysOnTopHint
                            # | Qt.CustomizeWindowHint
                            | Qt.X11BypassWindowManagerHint
                            # Qt.NoDropShadowWindowHint |
                            # Qt.BypassGraphicsProxyWidget
        )
        self.setAttribute(Qt.WA_X11NetWmWindowTypeDock, True)
                            # Qt.WindowDoesNotAcceptFocus)

        print(hex(int(self.windowFlags())))

    def mousePressEvent(self, qMouseEvent):
        if qMouseEvent.button() == Qt.LeftButton:
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
        app.mainWin.restore()
