# -*- coding: utf-8 -*-

from PyQt5.QtGui import QGuiApplication
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkDiskCache

class CustomNetworkAccessManager(QNetworkAccessManager):
    _cachePath = None

    def __init__(self, parent = None):
        super().__init__(parent)

        # set cache
        self._cachePath = QNetworkDiskCache(self)
        cacheLocation = QGuiApplication.instance().settings.get("frontend", "cachelocation")
        self._cachePath.setCacheDirectory(cacheLocation)
        self._cachePath.setMaximumCacheSize(20 * 1024 * 1024) # 20M
        self.setCache(self._cachePath)
