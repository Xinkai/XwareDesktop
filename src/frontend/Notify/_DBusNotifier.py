# -*- coding: utf-8 -*-


import logging
from launcher import app

from PyQt5.QtCore import QObject, pyqtSlot, QMetaType, QUrl, Qt
from PyQt5.QtDBus import QDBusConnection, QDBusInterface, QDBusArgument, QDBusMessage
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtMultimedia import QSound

from utils.system import systemOpen, viewOneFile

_DBUS_NOTIFY_SERVICE = "org.freedesktop.Notifications"
_DBUS_NOTIFY_PATH = "/org/freedesktop/Notifications"
_DBUS_NOTIFY_INTERFACE = "org.freedesktop.Notifications"


class Notifier(QObject):
    def __init__(self, parent):
        super().__init__(parent)
        self._conn = QDBusConnection("Xware Desktop").sessionBus()

        self._interface = QDBusInterface(_DBUS_NOTIFY_SERVICE,
                                         _DBUS_NOTIFY_PATH,
                                         _DBUS_NOTIFY_INTERFACE,
                                         self._conn)

        self._notified = {}  # a dict of notifyId: taskDict
        app.taskModel.taskCompleted.connect(self.notifyTaskCompleted, Qt.DirectConnection)

        self._capabilities = self._getCapabilities()
        if "actions" in self._capabilities:
            successful = self._conn.connect(_DBUS_NOTIFY_SERVICE,
                                            _DBUS_NOTIFY_PATH,
                                            _DBUS_NOTIFY_INTERFACE,
                                            "ActionInvoked", self.slotActionInvoked)
            if not successful:
                logging.error("ActionInvoked connect failed.")

        self._qSound_complete = QSound(":/sound/download-complete.wav", self)

    @property
    def isConnected(self):
        return self._conn.isConnected()

    @pyqtSlot("QObject", result = "void")
    def notifyTaskCompleted(self, taskItem):
        if app.settings.getbool("frontend", "notifybysound"):
            self._qSound_complete.play()

        if not app.settings.getbool("frontend", "popnotifications"):
            return

        self._dbus_notifyCompleted(taskItem)

    def _getCapabilities(self):
        # get libnotify server caps and remember it.
        qdBusMsg = self._interface.call(
            "GetCapabilities"
        )
        if qdBusMsg.errorName():
            logging.error("cannot get org.freedesktop.Notifications.GetCapabilities")
            return []
        else:
            return qdBusMsg.arguments()[0]

    def _dbus_notifyCompleted(self, task: "TaskItem"):
        if "actions" in self._capabilities:
            actions = QDBusArgument(["open", "打开", "viewOneFile", "在文件夹中显示"], QMetaType.QStringList)
        else:
            actions = QDBusArgument([], QMetaType.QStringList)

        qdBusMsg = self._interface.call(
            "Notify",
            QDBusArgument("Xware Desktop", QMetaType.QString),  # app_name
            QDBusArgument(0, QMetaType.UInt),  # replace_id
            QDBusArgument("xware-desktop", QMetaType.QString),  # app_icon
            QDBusArgument("下载完成", QMetaType.QString),  # summary
            QDBusArgument(task.name, QMetaType.QString),  # body
            actions,
            {
                "category": "transfer.complete",
            },  # hints
            QDBusArgument(5000, QMetaType.Int),  # timeout
        )

        if qdBusMsg.errorName():
            logging.error("DBus, notifyTask {}: {}".format(qdBusMsg.errorName(),
                                                           qdBusMsg.errorMessage()))
        else:
            # add it to the dict
            notificationId = qdBusMsg.arguments()[0]
            self._notified[notificationId] = task.id

    @pyqtSlot(QDBusMessage)
    def slotActionInvoked(self, msg):
        notifyId, action = msg.arguments()
        taskId = self._notified.get(notifyId, None)
        if not taskId:
            # other applications' notifications
            return

        taskItem = app.taskModel.taskManager.get(taskId, None)
        if not taskItem:
            logging.debug("taskItem cannot be found anymore in TaskModel.")
            return

        fullpath = taskItem.fullpath  # path + name

        if action == "open":
            return systemOpen(fullpath)
        elif action == "viewOneFile":
            return viewOneFile(fullpath)
        elif action == "default":  # Unity's notify osd always have a default action.
            return
        else:
            raise Exception("Unknown action from slotActionInvoked: {}.".format(action))
