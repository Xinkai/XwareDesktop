# -*- coding: utf-8 -*-

from launcher import app

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog
from .ui_taskproperty import Ui_Dialog
from Tasks.action import TaskCreation
from urllib import parse


class TaskPropertyDialog(QDialog, Ui_Dialog):
    def __init__(self, parent = None, model = None):
        super().__init__(parent)
        self.setupUi(self)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.treeSubTask.setModel(model)

        # load adapters
        for name in app.adapterManager.itr():
            adapter = app.adapterManager.adapter(name)
            self.combo_adapter.addItem(adapter.name, adapter)

    def accept(self):
        adapter = self.combo_adapter.currentData()
        creation = TaskCreation(parse.urlparse(self.line_url.text()))
        creation.path = self.combo_dir.currentText()
        if adapter.do_createTask(creation):
            super().accept()

    def reject(self):
        super().reject()
