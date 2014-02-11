# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QDialog
from ui_about import Ui_dlg_about

class AboutDialog(QDialog, Ui_dlg_about):
    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)

