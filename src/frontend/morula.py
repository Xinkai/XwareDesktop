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


from PyQt5.QtCore import pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import QApplication

import constants


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

        self.adapterManager = AdapterManager(taskModel = self.taskModel)
        for name, item in self.settings.itr_sections_with_prefix("adapter"):
            self.adapterManager.loadAdapter(item)

        from Tasks.action import TaskCreationAgent
        self.taskCreationAgent = TaskCreationAgent(self)
        self.taskCreationAgent.available.connect(self.slotCreateTask)
        self.taskCreationDlg = None

        from Services import SessionService
        self.sessionService = SessionService(self)

        from Widgets.Main import QmlMain
        self.qmlWin = QmlMain(None)
        self.qmlWin.show()
        self.aboutToQuit.connect(lambda: self.qmlWin.deleteLater())

    @pyqtSlot()
    def slotCreateTask(self):
        from Widgets.TaskProperty import TaskPropertyDialog
        from models.TaskTreeModel import TaskTreeModel
        creationModel = TaskTreeModel(self)
        self.taskCreationDlg = TaskPropertyDialog(model = creationModel,
                                                  parent = None)
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
