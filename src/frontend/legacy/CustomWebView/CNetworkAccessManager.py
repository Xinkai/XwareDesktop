# -*- coding: utf-8 -*-

import logging
from launcher import app

from PyQt5.QtCore import QUrlQuery
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkDiskCache

import os


def forLocalDeviceOnly(func):
    def wrapper(SELF, request):
        # Looking for Pid in query string, try matching with locally bound peerid
        localPeerId = app.adapterManager[0].peerId
        if not localPeerId:
            return request

        urlQuery = QUrlQuery(request.url())
        queryItems = dict(urlQuery.queryItems())
        if queryItems.get("pid", None) != localPeerId:
            return request
        return func(SELF, request)
    return wrapper


class CustomNetworkAccessManager(QNetworkAccessManager):
    def __init__(self, parent = None):
        super().__init__(parent)
        # set cache
        self._cachePath = QNetworkDiskCache(self)
        cacheLocation = app.settings.myGet("legacy", "cachelocation")
        self._cachePath.setCacheDirectory(cacheLocation)
        self._cachePath.setMaximumCacheSize(20 * 1024 * 1024)  # 20M
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

    @staticmethod
    def _redirectToLocal(request):
        qurl = request.url()
        adapter = app.adapterManager[0]
        host = adapter._xwareClient._options.get("host", "127.0.0.1")
        port = int(adapter._xwareClient._options.get("port", 9000))
        qurl.setHost(host)
        qurl.setPort(port)
        request.setUrl(qurl)
        return request

    @staticmethod
    def _preprocess_request_bind(request):
        # set boxName when binding the device to hostname

        urlQuery = QUrlQuery(request.url())
        queryItems = urlQuery.queryItems()

        for i, item in enumerate(queryItems):
            if item[0] == "boxName":
                queryItems[i] = ("boxName", os.uname().nodename)
        queryItems.append(("ct", "0"),)  # Issue #109, Xunlei bind API changed
        urlQuery.setQueryItems(queryItems)

        # write changes back to request
        qurl = request.url()
        qurl.setQuery(urlQuery)
        request.setUrl(qurl)

        return request

    @forLocalDeviceOnly
    def _preprocess_request_boxSpace(self, request):
        request = self._redirectToLocal(request)
        return request
