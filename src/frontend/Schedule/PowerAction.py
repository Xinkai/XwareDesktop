# -*- coding: utf-8 -*-

import logging

from PyQt5.QtCore import QObject
from PyQt5.QtDBus import QDBusConnection, QDBusInterface
from PyQt5.QtWidgets import QApplication
import os

_DBUS_POWER_SERVICE = "org.freedesktop.login1"
_DBUS_POWER_PATH = "/org/freedesktop/login1"
_DBUS_POWER_INTERFACE = "org.freedesktop.login1.Manager"

ACTION_NONE = 0
ACTION_POWEROFF = 1
ACTION_HYBRIDSLEEP = 2
ACTION_HIBERNATE = 3
ACTION_SUSPEND = 4


class PowerAction(object):
    # defines a power action
    manager = None
    actionId = None
    displayName = None
    internalName = None
    availability = None
    command = None

    def __init__(self, manager, actionId, displayName, internalName):
        super().__init__()
        self.manager = manager
        self.actionId = actionId
        self.displayName = displayName
        self.internalName = internalName
        settings = QApplication.instance().settings
        if self.actionId == ACTION_NONE:
            # always allow doing nothing
            availability = "yes"
            command = None
        else:
            optionKey = self.internalName.lower() + "cmd"
            if settings.has("scheduler", optionKey):
                # override action with command
                availability = "cmd"
                command = settings.get("scheduler", optionKey)
                # TODO: check if the command is bad.
            else:
                # use the default action, namely logind.
                # needs to check for availability
                msg = self.manager._interface.call("Can" + self.internalName)
                availability = msg.arguments()[0]
                command = None

        self.availability = availability
        self.command = command

    def __repr__(self):
        contents = [
            "{}({})".format(self.internalName, self.actionId),
            self.availability,
        ]
        if self.command is not None:
            contents.append(self.command)

        return "{cls}<{contents}>".format(
            cls = self.__class__.__name__,
            contents = ":".join(contents))


class PowerActionManager(QObject):
    # manages power actions, and act them.
    _conn = None
    _interface = None
    actions = None

    def __init__(self, parent = None):
        super().__init__(parent)
        self._conn = QDBusConnection("Xware Desktop").systemBus()
        self._interface = QDBusInterface(_DBUS_POWER_SERVICE,
                                         _DBUS_POWER_PATH,
                                         _DBUS_POWER_INTERFACE,
                                         self._conn)

        self.actions = (
            PowerAction(self, ACTION_NONE, "无", "None"),
            PowerAction(self, ACTION_POWEROFF, "关机", "PowerOff"),
            PowerAction(self, ACTION_HYBRIDSLEEP, "混合休眠", "HybridSleep"),
            PowerAction(self, ACTION_HIBERNATE, "休眠", "Hibernate"),
            PowerAction(self, ACTION_SUSPEND, "睡眠", "Suspend"),
        )
        logging.info(self.actions)

    def getActionById(self, actionId):
        return self.actions[actionId]

    def act(self, actionId):
        action = self.getActionById(actionId)
        if action.command:
            return self._cmdAct(action)
        elif action.availability == "yes":
            return self._dbusAct(action)
        raise Exception("Unhandled {}".format(action))

    def _dbusAct(self, action):
        logging.info("scheduler is about to act: {}".format(action))
        msg = self._interface.call(action.internalName,
                                   False)
        if msg.errorName():
            logging.error(msg.errorMessage())

    @staticmethod
    def _cmdAct(action):
        logging.info("scheduler is about to execute: {}".format(action))
        os.system(action.command)
