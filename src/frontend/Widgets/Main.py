# -*- coding: utf-8 -*-

import os, constants

from PyQt5.QtCore import QCoreApplication, QUrl, QSize
from PyQt5.QtQuick import QQuickView
from Widgets.QuickView import CustomQuickView

from utils.IconProvider import IconProvider, MimeIconProvider


class QmlMain(CustomQuickView):
    def __init__(self, parent):
        super().__init__(parent)
        app = QCoreApplication.instance()

        self.setTitle("Xware Desktop with QML (experimental)")
        self.setResizeMode(QQuickView.SizeRootObjectToView)
        self.qmlUrl = QUrl.fromLocalFile(os.path.join(constants.FRONTEND_DIR, "QML/Main.qml"))
        self._iconProvider = IconProvider()
        self._mimeIconProvider = MimeIconProvider()
        self.engine().addImageProvider("icon", self._iconProvider)
        self.engine().addImageProvider("mimeicon", self._mimeIconProvider)
        self.rootContext().setContextProperty("adapters", app.adapterManager)
        self.rootContext().setContextProperty("taskModel", app.proxyModel)
        self.rootContext().setContextProperty("schedulerModel", app.schedulerModel)
        self.rootContext().setContextProperty("taskCreationAgent", app.taskCreationAgent)
        self.setSource(self.qmlUrl)
        self.resize(QSize(800, 600))
