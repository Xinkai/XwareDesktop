# -*- coding: utf-8 -*-

from launcher import app

import collections
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import QDialog, QFileDialog
from .ui_taskproperty import Ui_Dialog
from Tasks.action import TaskCreation
from urllib import parse
import os


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

        self.recentdirs = collections.deque(
            filter(bool, app.settings.get("internal", "recentsavedirs").split("\t")),
            maxlen = app.settings.getint("internal", "recentsavedirscount")
        )

        self.combo_dir.addItems(list(self.recentdirs))

    @pyqtSlot()
    def on_btn_localUpload_clicked(self):
        folder = app.settings.get("internal", "lastlocaluploaddir")
        if not folder:
            folder = os.path.expanduser("~/Downloads")

        dlg = QFileDialog(self,
                          "选择本地种子/Metalink文件",
                          folder,
                          "种子/Metalink (*.torrent *.metalink *.meta4)")
        dlg.setFileMode(QFileDialog.ExistingFile)
        if dlg.exec():
            selectedFile = dlg.selectedFiles()[0]
            app.settings.set("internal",
                             "lastlocaluploaddir",
                             os.path.dirname(selectedFile))
            self.line_url.setText(selectedFile)

    @pyqtSlot(str)
    def on_line_url_textChanged(self, value):
        print("TODO: line_url changed to {}".format(value))

    def accept(self):
        adapter = self.combo_adapter.currentData()
        creation = TaskCreation(parse.urlparse(self.line_url.text()))
        creation.path = self.combo_dir.currentText()

        try:
            self.recentdirs.remove(creation.path)
        except ValueError:  # not found
            pass
        self.recentdirs.append(creation.path)
        app.settings.set("internal", "recentsavedirs", "\t".join(self.recentdirs))

        if adapter.do_createTask(creation):
            super().accept()

    def reject(self):
        super().reject()
