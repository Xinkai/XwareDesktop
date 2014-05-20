# -*- coding: utf-8 -*-

from launcher import app

from PyQt5.QtCore import pyqtSlot


# On Ubuntu 13.10 (Qt5.0) when lastWindowClosed emits, some non-main windows don't quit.
class TeardownHelper(object):
    def __init__(self, *args, **kwargs):
        app.lastWindowClosed.connect(self.teardown)
        self.destroyed.connect(self.cancelTeardown)

    # @pyqtSlot()
    def teardown(self):
        self.destroy()

    def cancelTeardown(self):
        app.lastWindowClosed.disconnect(self.teardown)
