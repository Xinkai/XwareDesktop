# -*- coding: utf-8 -*-

from PyQt5.QtCore import pyqtSlot, Qt, QUrl
from PyQt5.QtGui import QDropEvent
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWebKit import QWebSettings
from PyQt5.QtWebKitWidgets import QWebView

import constants
from .CWebPage import CustomWebPage

class CustomWebView(QWebView):
    app = None
    _customPage = None

    def __init__(self, parent):
        super().__init__(parent)
        self.app = QApplication.instance()
        self._customPage = CustomWebPage(self)
        self.setPage(self._customPage)
        self.app.settings.applySettings.connect(self.slotApplySettings)
        self.load(QUrl(constants.LOGIN_PAGE))

    @pyqtSlot(QDropEvent)
    def dropEvent(self, qEvent):
        print(self.__class__.__name__, "stopped dropEvent.")
        # TODO: implement drop.

    @pyqtSlot()
    def slotApplySettings(self):
        isDevToolsAllowed = self.app.settings.getbool("frontend", "enabledeveloperstools")
        self.settings().setAttribute(QWebSettings.DeveloperExtrasEnabled, isDevToolsAllowed)
        if isDevToolsAllowed:
            self.setContextMenuPolicy(Qt.DefaultContextMenu)
        else:
            self.setContextMenuPolicy(Qt.NoContextMenu)

        pluginsAllowed = self.app.settings.getbool("frontend", "allowflash")
        self.settings().setAttribute(QWebSettings.PluginsEnabled, pluginsAllowed)
        self.app.frontendpy.sigToggleFlashAvailability.emit(pluginsAllowed)
