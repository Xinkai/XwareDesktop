# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QSystemTrayIcon
from Compat.TeardownHelper import TeardownHelper

# On Ubuntu 13.10, systrayicon won't destroy itself gracefully, stops the whole program from exiting.
# hiding it works around the problem
class CompatSystemTrayIcon(QSystemTrayIcon, TeardownHelper):
    def __init__(self, parent = None):
        super().__init__(parent)

    def teardown(self):
        self.setVisible(False)
