#!/usr/bin/python3 -OO
# -*- coding: utf-8 -*-

import os, sys

if __name__ == "__main__":
    if sys.platform == "linux":
        if os.getuid() == 0:
            print("拒绝以root执行。", file = sys.stderr)
            sys.exit(1)

    sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../"))
    sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 "../shared/thirdparty"))

    import faulthandler
    faultLogFd = open(os.path.expanduser('~/.xware-desktop/profile/frontend.fault.log'), 'a')
    faulthandler.enable(faultLogFd)


from PyQt5.QtCore import QUrl, QSize, pyqtSlot, pyqtSignal
from PyQt5.QtQuick import QQuickView
from PyQt5.QtWidgets import QApplication

from Widgets.QuickView import CustomQuickView

import constants
from utils.IconProvider import IconProvider, MimeIconProvider


class QmlMain(CustomQuickView):
    def __init__(self, parent):
        super().__init__(parent)
        app = QApplication.instance()

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


class DummyApp(QApplication):
    applySettings = pyqtSignal()

    def __init__(self, *args):
        super().__init__(*args)

        from shared.config import SettingsAccessorBase
        from Settings import DEFAULT_SETTINGS
        self.settings = SettingsAccessorBase(constants.FRONTEND_CONFIG_FILE,
                                             DEFAULT_SETTINGS)
        self.aboutToQuit.connect(lambda: self.settings.save())

        from models import TaskModel, AdapterManager, ProxyModel
        from Schedule.model import SchedulerModel

        self.taskModel = TaskModel()
        self.proxyModel = ProxyModel()
        self.proxyModel.setSourceModel(self.taskModel)
        self.schedulerModel = SchedulerModel(self)
        self.schedulerModel.setSourceModel(self.taskModel)

        self.adapterManager = AdapterManager()
        for name, item in self.settings.itr_sections_with_prefix("adapter"):
            self.adapterManager.loadAdapter(item)

        from Tasks.action import TaskCreationAgent
        self.taskCreationAgent = TaskCreationAgent(self)
        self.taskCreationAgent.available.connect(self.slotCreateTask)
        self.taskCreationDlg = None

        self.qmlWin = QmlMain(None)
        self.qmlWin.show()
        self.aboutToQuit.connect(lambda: self.qmlWin.deleteLater())

    @pyqtSlot()
    def slotCreateTask(self):
        from Widgets.TaskProperty import TaskPropertyDialog
        self.taskCreationDlg = TaskPropertyDialog(None)
        self.taskCreationDlg.show()

from PyQt5.QtCore import QtMsgType, QMessageLogContext, QtDebugMsg, QtWarningMsg, QtCriticalMsg, \
    QtFatalMsg


def installQtMsgHandler(msgType: QtMsgType, context: QMessageLogContext, msg: str):
    strType = {
        QtDebugMsg: "DEBUG",
        QtWarningMsg: "WARN",
        QtCriticalMsg: "CRITICAL",
        QtFatalMsg: "FATAL"
    }[msgType]

    print("Qt[{strType}] {category} {function} in {file}, on line {line}\n"
          "    {msg}".format(strType = strType,
                             category = context.category,
                             function = context.function,
                             file = context.file,
                             line = context.line,
                             msg = msg),
          file = sys.stdout if msgType in (QtDebugMsg, QtWarningMsg) else sys.stderr)


if __name__ == "__main__":
    from PyQt5.QtCore import qInstallMessageHandler
    qInstallMessageHandler(installQtMsgHandler)
    app = DummyApp(sys.argv)

    def safeExec(app_):
        code = app_.exec()
        if __debug__:
            windows = app_.topLevelWindows()
            if windows:
                raise RuntimeError("Windows left: {}"
                                   .format(list(map(lambda win: win.objectName(),
                                                    windows))))
            widgets = app_.topLevelWidgets()
            if widgets:
                raise RuntimeError("Widgets left: {}"
                                   .format(list(map(lambda wid: wid.objectName(),
                                                    widgets))))
        del app_
        sys.exit(code)
    safeExec(app)
