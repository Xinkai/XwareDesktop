# -*- coding: utf-8 -*-

import logging
from launcher import app

from PyQt5.QtCore import pyqtSlot, Qt, QUrl, QSize
from PyQt5.QtGui import QDropEvent
from PyQt5.QtWebKit import QWebSettings
from PyQt5.QtWebKitWidgets import QWebView

import constants
from .CWebPage import CustomWebPage


class CustomWebView(QWebView):
    _customPage = None

    def __init__(self, parent):
        super().__init__(parent)
        self._customPage = CustomWebPage(self)
        self.setPage(self._customPage)
        app.settings.applySettings.connect(self.slotApplySettings)
        self.load(QUrl(constants.LOGIN_PAGE))

    @pyqtSlot(QDropEvent)
    def dropEvent(self, qEvent):
        print(self.__class__.__name__, "stopped dropEvent.")
        # TODO: implement drop.

    @pyqtSlot()
    def slotApplySettings(self):
        isDevToolsAllowed = app.settings.getbool("frontend", "enabledeveloperstools")
        self.settings().setAttribute(QWebSettings.DeveloperExtrasEnabled, isDevToolsAllowed)
        if isDevToolsAllowed:
            self.setContextMenuPolicy(Qt.DefaultContextMenu)
        else:
            self.setContextMenuPolicy(Qt.NoContextMenu)

        pluginsAllowed = app.settings.getbool("frontend", "allowflash")
        self.settings().setAttribute(QWebSettings.PluginsEnabled, pluginsAllowed)
        app.frontendpy.sigToggleFlashAvailability.emit(pluginsAllowed)

        zoom = app.settings.get("frontend", "webviewzoom")
        if zoom:
            zoom = float(zoom)
            self.setZoomFactor(zoom)

        minimumSizeOverride = app.settings.get("frontend", "webviewminsizeoverride")
        if minimumSizeOverride:
            w, h = minimumSizeOverride.split(",")
            w, h = int(w), int(h)
        else:
            w, h = 1008, 715

        self.setMinimumSize(QSize(w, h))
