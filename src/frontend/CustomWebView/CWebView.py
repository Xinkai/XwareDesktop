# -*- coding: utf-8 -*-

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QDropEvent
from PyQt5.QtWebKitWidgets import QWebView

from .CWebPage import CustomWebPage

class CustomWebView(QWebView):
    _customPage = None

    def __init__(self, parent):
        super().__init__(parent)
        self._customPage = CustomWebPage(self)
        self.setPage(self._customPage)

    @pyqtSlot(QDropEvent)
    def dropEvent(self, qEvent):
        print(self.__class__.__name__, "stopped dropEvent.")
        # TODO: implement drop.
