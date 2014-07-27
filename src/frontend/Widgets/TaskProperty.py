# -*- coding: utf-8 -*-

from launcher import app

from PyQt5.QtWidgets import QDialog
from Widgets.ui_taskproperty import Ui_Dialog


class TaskPropertyDialog(QDialog, Ui_Dialog):
    def __init__(self, parent = None, model = None):
        super().__init__(parent)
        self.setupUi(self)
        self.treeSubTask.setModel(model)
