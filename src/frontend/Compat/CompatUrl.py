# -*- coding: utf-8 -*-

import logging

from PyQt5.QtCore import QUrl
from urllib.parse import urlparse

class CompatUrl(QUrl):
    def __init__(self, *args):
        super().__init__(*args)
        if not hasattr(self, "fileName"):
            self.fileName = self._fileName

    def _fileName(self):
        # Introduced in Qt 5.2
        url = self.toString()
        urlPath = urlparse(url).path
        fileName = urlPath.split("/")[-1]
        return fileName
