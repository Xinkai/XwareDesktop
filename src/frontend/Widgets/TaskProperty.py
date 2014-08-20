# -*- coding: utf-8 -*-

from launcher import app

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog
from .ui_taskproperty import Ui_Dialog


class TaskPropertyDialog(QDialog, Ui_Dialog):
    def __init__(self, parent = None, model = None):
        super().__init__(parent)
        self.setupUi(self)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.treeSubTask.setModel(model)
