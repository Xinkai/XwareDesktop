# -*- coding: utf-8 -*-

import logging
from launcher import app

from misc import debounce


# A helper to automatically preserve the geometry of windows.
# Usage: Inherit PersistentGeometry, and then call preserveGeometry()
class PersistentGeometry(object):
    def preserveGeometry(self):
        savedGeometry = app.settings.getobj("internal", self._geometryKeyname())
        if savedGeometry:
            self.restoreGeometry(savedGeometry)

    @debounce(0.2, instant_first = False)
    def _setGeometry(self):
        app.settings.setobj("internal",
                            self._geometryKeyname(),
                            self.saveGeometry())

    def moveEvent(self, qMoveEvent):
        self._setGeometry()
        super(self.__class__, self).moveEvent(qMoveEvent)

    def resizeEvent(self, qResizeEvent):
        self._setGeometry()
        super(self.__class__, self).resizeEvent(qResizeEvent)

    def _geometryKeyname(self):
        return self.objectName().lower() + "geometry"
