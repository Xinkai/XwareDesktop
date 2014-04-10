# -*- coding: utf-8 -*-

import logging

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel


class CustomStatusBarLabel(QLabel):
    def __init__(self, parent):
        super().__init__(parent)
        self.setTextFormat(Qt.RichText)
        parent.addPermanentWidget(self)
