# -*- coding: utf-8 -*-

import logging

from PyQt5.QtWidgets import QPushButton, QApplication

class CustomStatusBarButton(QPushButton):
    app = None
    def __init__(self, parent):
        super().__init__(parent)
        self.app = QApplication.instance()
        parent.addPermanentWidget(self)

