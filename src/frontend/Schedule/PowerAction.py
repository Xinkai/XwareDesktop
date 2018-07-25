# -*- coding: utf-8 -*-

import logging
from launcher import app

from PyQt5.QtCore import QObject
from PyQt5.QtDBus import QDBusConnection, QDBusInterface
import os
import enum
from . import Action

_DBUS_POWER_SERVICE = "org.freedesktop.login1"
_DBUS_POWER_PATH = "/org/freedesktop/login1"
_DBUS_POWER_INTERFACE = "org.freedesktop.login1.Manager"


@enum.unique
class ActionType(enum.Enum):
    Special = 0
    Command = 1
    DBus = 2


class PowerActionManager(QObject):
    def __init__(self, parent = None):
        # manages power actions, and act them.
        super().__init__(parent)
        self._conn = QDBusConnection("Xware Desktop").systemBus()
        self._interface = QDBusInterface(_DBUS_POWER_SERVICE,
                                         _DBUS_POWER_PATH,
                                         _DBUS_POWER_INTERFACE,
                                         self._conn)

        self._actions = {}  # {Action: ActionType}
        self._loadActions()

    def _loadActions(self):
        for action in Action:
            # Always allow Null action
            if action == Action.Null:
                self._actions[action] = ActionType.Special
                continue

            # check if cmd is set
            internalName = action.name
            if app.settings.has("scheduler", internalName + "cmd"):
                self._actions[action] = ActionType.Command
                continue

            # check if logind supports it
            msg = self._interface.call("Can" + internalName)
            if msg.errorName():
                logging.error(msg.errorMessage())
            availability = msg.arguments()[0]
            if availability == "yes":
                self._actions[action] = ActionType.DBus
                continue

    @property
    def actions(self) -> "listlike of actions":
        return self._actions.keys()

    def act(self, action: Action):
        assert isinstance(action, Action), "{} is not an Action".format(action)
        assert action in self._actions, "{} is not available!".format(action)
        actionType = self._actions.get(action, None)
        internalName = action.name
        if actionType is None:
            raise ValueError("{} are not supported!".format(action))
        if actionType == ActionType.Special:
            raise ValueError("Cannot act on {}".format(action))
        elif actionType == ActionType.Command:
            cmd = app.settings.myGet("scheduler", internalName + "cmd")
            os.system(cmd)
            return
        elif actionType == ActionType.DBus:
            msg = self._interface.call(internalName, False)
            if msg.errorName():
                logging.error(msg.errorMessage())
            return
        else:
            raise ValueError("Unhandled {}".format(action))
