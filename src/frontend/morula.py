# -*- coding: utf-8 -*-
import os, sys
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../"))

from PyQt5.QtCore import QUrl, QSize
from PyQt5.QtQuick import QQuickView
from PyQt5.QtGui import QGuiApplication

from Widgets import CustomQuickView


class QmlMain(CustomQuickView):
    def __init__(self, parent):
        super().__init__(parent)
        app = QGuiApplication.instance()

        self.setTitle("Xware Desktop with QML (experimental)")
        self.setResizeMode(QQuickView.SizeRootObjectToView)
        self.qmlUrl = QUrl.fromLocalFile("QML/Main.qml")
        self.rootContext().setContextProperty("adapters", app.adapterManager)
        self.rootContext().setContextProperty("taskModel", app.proxyModel)
        self.setSource(self.qmlUrl)
        self.resize(QSize(800, 600))


class DummyApp(QGuiApplication):
    def __init__(self, *args):
        super().__init__(*args)

        from models import TaskModel, AdapterManager, ProxyModel
        from libxware import XwareAdapterThread

        self.taskModel = TaskModel()
        self.proxyModel = ProxyModel()
        self.proxyModel.setSourceModel(self.taskModel)

        self.adapterManager = AdapterManager()
        self.xwareAdapterThread = XwareAdapterThread({
            "host": "127.0.0.1",
            "port": 9000,
        })
        self.xwareAdapterThread.start()

        self.qmlWin = QmlMain(None)
        self.qmlWin.show()

if __name__ == "__main__":
    app = DummyApp(sys.argv)
    sys.exit(app.exec())
