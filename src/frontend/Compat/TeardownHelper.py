# -*- coding: utf-8 -*-

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QApplication

# On Ubuntu 13.10 (Qt5.0) when lastWindowClosed emits, some non-main windows doesn't quit.
class TeardownHelper(object):
    def __init__(self, *args, **kwargs):
        QApplication.instance().lastWindowClosed.connect(self.teardown)

    # @pyqtSlot()
    def teardown(self):
        self.destroy()
