# -*- coding: utf-8 -*-

import logging

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QPushButton, QApplication, QToolButton


class CustomStatusBarButton(QPushButton):
    app = None

    def __init__(self, parent):
        super().__init__(parent)
        self.app = QApplication.instance()
        parent.addPermanentWidget(self)


class CustomStatusBarToolButton(QToolButton):
    app = None

    def __init__(self, parent):
        super().__init__(parent)
        self.app = QApplication.instance()
        self.setStyleSheet("::menu-indicator { image: none }")
        self.setToolButtonStyle(Qt.ToolButtonFollowStyle)
        self.setPopupMode(QToolButton.InstantPopup)
        self.setArrowType(Qt.DownArrow)

        parent.addPermanentWidget(self)
