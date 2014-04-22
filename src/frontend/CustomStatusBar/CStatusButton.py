# -*- coding: utf-8 -*-

import logging

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QPushButton, QToolButton


class CustomStatusBarButton(QPushButton):
    def __init__(self, parent):
        super().__init__(parent)
        parent.addPermanentWidget(self)


class CustomStatusBarToolButton(QToolButton):
    def __init__(self, parent):
        super().__init__(parent)
        self.setStyleSheet("::menu-indicator { image: none }")
        self.setToolButtonStyle(Qt.ToolButtonFollowStyle)
        self.setPopupMode(QToolButton.InstantPopup)
        self.setArrowType(Qt.DownArrow)

        parent.addPermanentWidget(self)
