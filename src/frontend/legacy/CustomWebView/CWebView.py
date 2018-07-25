# -*- coding: utf-8 -*-

import logging
from launcher import app
import sys
from PyQt5.QtCore import pyqtSlot, Qt, QUrl, QSize
from PyQt5.QtGui import QDropEvent

from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebEngineWidgets import QWebEngineSettings
from PyQt5.QtWebChannel import QWebChannel

import constants
from .CWebPage import CustomWebPage

class CustomWebView(QWebEngineView):
    def __init__(self, parent):
        super().__init__(parent)
        self._customPage = CustomWebPage(self)
        self.setPage(self._customPage)

        app.applySettings.connect(self.slotApplySettings)
        self.load(QUrl(constants.LOGIN_PAGE))

    @pyqtSlot(QDropEvent)
    def dropEvent(self, qEvent):
        print(self.__class__.__name__, "stopped dropEvent.")
        # TODO: implement drop.

    @pyqtSlot()
    def slotApplySettings(self):
        isDevToolsAllowed = app.settings.getbool("legacy", "enabledeveloperstools")
        #self.settings().setAttribute(QWebEngineSettings.globalSettings().WebGLEnabled, isDevToolsAllowed)
        if isDevToolsAllowed:
            self.setContextMenuPolicy(Qt.DefaultContextMenu)
        else:
            self.setContextMenuPolicy(Qt.NoContextMenu)
        pluginsAllowed = app.settings.getbool("legacy", "allowflash")
        self.settings().setAttribute(QWebEngineSettings.PluginsEnabled, pluginsAllowed)
        app.frontendpy.sigToggleFlashAvailability.emit(pluginsAllowed)

        zoom = app.settings.myGet("legacy", "webviewzoom")
        if zoom:
            zoom = float(zoom)
            self.setZoomFactor(zoom)

        minimumSizeOverride = app.settings.myGet("legacy", "webviewminsizeoverride")
        if minimumSizeOverride:
            w, h = minimumSizeOverride.split(",")
            w, h = int(w), int(h)
        else:
            w, h = 1008, 715

        self.setMinimumSize(QSize(w, h))
