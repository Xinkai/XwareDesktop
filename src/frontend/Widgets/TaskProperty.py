# -*- coding: utf-8 -*-

import logging
from launcher import app

import collections
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import QDialog, QFileDialog
from .ui_taskproperty import Ui_Dialog
from Tasks.action import TaskCreation
from models.TaskTreeModel import TaskTreeModel, TaskTreeModelMode
from urllib import parse
import os

_NamespaceRole = Qt.UserRole + 0x2BAD


class TaskPropertyDialog(QDialog, Ui_Dialog):
    def __init__(self, model: TaskTreeModel, parent = None):
        super().__init__(parent)
        self.setupUi(self)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.model = model
        self.treeSubTask.setModel(model)

        if self.model.mode == TaskTreeModelMode.Creation:
            self.setWindowTitle("新建任务")

            # load adapters
            for i, namespace in enumerate(app.adapterManager.itr()):
                adapter = app.adapterManager.adapter(namespace)
                self.combo_adapter.addItem(adapter.name, adapter)
                self.combo_adapter.setItemData(i, namespace, _NamespaceRole)
            lastAdapterUsed = app.settings.myGet("internal", "lastadapterused")
            if lastAdapterUsed:
                index = self.combo_adapter.findData(lastAdapterUsed, _NamespaceRole)
                if index != -1:
                    self.combo_adapter.setCurrentIndex(index)

            self.recentdirs = collections.deque(
                filter(bool, app.settings.myGet("internal", "recentsavedirs").split("\t")),
                maxlen = app.settings.getint("internal", "recentsavedirscount")
            )
            self.combo_dir.addItems(list(self.recentdirs))

        else:
            self.line_url.setEnabled(False)
            self.combo_adapter.setEnabled(False)
            self.combo_dir.setEnabled(False)

    @pyqtSlot()
    def on_btn_localUpload_clicked(self):
        folder = app.settings.myGet("internal", "lastlocaluploaddir")
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
        self.invalidateTreeModel()

    @pyqtSlot(int)
    def on_combo_adapter_activated(self, _):
        self.invalidateTreeModel()

    def invalidateTreeModel(self):
        self.buttonBox.setEnabled(False)
        print("invalidate treemodel")
        adapter = self.combo_adapter.currentData()
        url = self.line_url.text()
        parsed = parse.urlparse(url)

        creation = TaskCreation(parsed)
        if creation.kind in adapter.__class__.Manifest["SupportedTypes"]:
            ok, error = self.model.fromCreation(creation)
        else:
            ok = False
            error = "Not supported by this adapter."

        if ok:
            self.buttonBox.setEnabled(True)
        else:
            logging.error(error)

    def accept(self):
        if not self.model.mode == TaskTreeModelMode.Creation:
            super().reject()

        adapter = self.combo_adapter.currentData()
        creation = self.model.toCreation()
        creation.path = self.combo_dir.currentText()

        ok, error = adapter.do_createTask(creation)
        if ok:
            # remember recent save dirs
            try:
                self.recentdirs.remove(creation.path)
            except ValueError:  # not found
                pass
            self.recentdirs.appendleft(creation.path)
            app.settings.set("internal", "recentsavedirs", "\t".join(self.recentdirs))

            # remember last adapter used
            app.settings.set("internal",
                             "lastadapterused",
                             self.combo_adapter.currentData(_NamespaceRole))

            super().accept()
        else:
            logging.error(error)

    def reject(self):
        super().reject()
