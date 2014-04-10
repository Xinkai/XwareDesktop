# -*- coding: utf-8 -*-

import logging

from PyQt5.QtWidgets import QApplication
from misc import debounce


# A helper to automatically preserve the geometry of windows.
# Usage: Inherit PersistentGeometry, and then call preserveGeometry(keyname)
class PersistentGeometry(object):
    _persistent_geometry_name = None

    def preserveGeometry(self, keyname):
        app = QApplication.instance()
        savedGeometry = app.settings.getobj("frontend", "{}wingeometry".format(keyname))
        if savedGeometry:
            self.restoreGeometry(savedGeometry)
        self._persistent_geometry_name = keyname

    @debounce(0.2, instant_first = False)
    def _setGeometry(self):
        QApplication.instance().settings.setobj(
            "frontend",
            "{}wingeometry".format(self._persistent_geometry_name),
            self.saveGeometry())

    def moveEvent(self, qMoveEvent):
        if getattr(self, "_persistent_geometry_name", False):
            self._setGeometry()
        super(self.__class__, self).moveEvent(qMoveEvent)

    def resizeEvent(self, qResizeEvent):
        if getattr(self, "_persistent_geometry_name", False):
            self._setGeometry()
        super(self.__class__, self).resizeEvent(qResizeEvent)
