# -*- coding: utf-8 -*-

from PyQt5.QtCore import QObject
from PyQt5.QtDBus import QDBusConnection, QDBusInterface

import constants


class DBusService(QObject):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.sessionBus = QDBusConnection.sessionBus()
        self._dbusInterface = QDBusInterface("org.freedesktop.DBus",
                                             "/",
                                             "org.freedesktop.DBus")

        if self.serviceExists(self.serviceName):
            raise RuntimeError("There's a DBus that has the same name.")

        created = self.sessionBus.registerService(self.serviceName)
        if not created:
            raise RuntimeError("Cannot create DBus Service.")
        self.registerObject("/", self)

    def registerObject(self, path: str, adapter: QObject):
        return self.sessionBus.registerObject(
            path,
            adapter,
            QDBusConnection.ExportAllSlots | QDBusConnection.ExportAllProperties |
            QDBusConnection.ExportAllSignals,
        )

    @property
    def serviceName(self):
        return constants.DBUS_SESSION_SERVICE

    def serviceExists(self, name) -> bool:
        msg = self._dbusInterface.call(
            "ListNames",
        )
        return name in msg.arguments()[0]
