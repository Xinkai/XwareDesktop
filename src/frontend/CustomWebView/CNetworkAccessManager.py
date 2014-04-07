# -*- coding: utf-8 -*-

from PyQt5.QtCore import QUrlQuery
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkDiskCache
from PyQt5.QtWidgets import QApplication

class CustomNetworkAccessManager(QNetworkAccessManager):
    _cachePath = None

    def __init__(self, parent = None):
        super().__init__(parent)

        # set cache
        self._cachePath = QNetworkDiskCache(self)
        cacheLocation = QApplication.instance().settings.get("frontend", "cachelocation")
        self._cachePath.setCacheDirectory(cacheLocation)
        self._cachePath.setMaximumCacheSize(20 * 1024 * 1024) # 20M
        self.setCache(self._cachePath)

    def createRequest(self, op, request, device = None):
        qurl = request.url()
        if qurl.host() == "homecloud.yuancheng.xunlei.com":
            path = qurl.fileName()
            preprocessor = self.getPreprocessorFor(path)
            if preprocessor:
                request = preprocessor(request)

        return super().createRequest(op, request, device)

    def getPreprocessorFor(self, path):
        return getattr(self, "_preprocess_request_{}".format(path), None)

    def _preprocess_request_bind(self, request):
        # set boxName when binding the device to hostname
        import os

        urlQuery = QUrlQuery(request.url())
        queryItems = urlQuery.queryItems()

        for i, item in enumerate(queryItems):
            if item[0] == "boxName":
                queryItems[i] = ("boxName", os.uname().nodename)
        urlQuery.setQueryItems(queryItems)

        # write changes back to request
        qurl = request.url()
        qurl.setQuery(urlQuery)
        request.setUrl(qurl)

        return request
