# -*- coding: utf-8 -*-

import logging
from launcher import app

from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtWidgets import QDialog

from PersistentGeometry import PersistentGeometry
from .ui_scheduler import Ui_SchedulerDialog
from Schedule import ActWhen, Action


class SchedulerWindow(QDialog, Ui_SchedulerDialog, PersistentGeometry):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setupUi(self)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.preserveGeometry()

        # actWhen ComboBox
        for row, actWhen in enumerate(ActWhen.__members__.values()):
            self.comboBox_actWhen.addItem(str(actWhen))
            self.comboBox_actWhen.setItemData(row, int(actWhen))

        self.slotActWhenChanged(app.schedulerModel.actWhen)
        self.comboBox_actWhen.setCurrentIndex(app.schedulerModel.actWhen)
        self.comboBox_actWhen.activated[int].connect(self.slotActWhenChanged)

        # ListView
        self.listView_runningTasks.setSelectionMode(self.listView_runningTasks.ExtendedSelection)
        self.listView_runningTasks.setModel(app.schedulerModel)
        self.listView_runningTasks.setSelectionModel(app.schedulerModel.selectionModel)

        # action comboBox
        for row, action in enumerate(app.schedulerModel.actions):
            self.comboBox_action.addItem(str(action))
            self.comboBox_action.setItemData(row, int(action))
        index = self.comboBox_action.findData(int(app.schedulerModel.action))
        self.comboBox_action.setCurrentIndex(index)

    @pyqtSlot(int)
    def slotActWhenChanged(self, choice):
        if choice == ActWhen.ALL_TASKS_COMPLETED:
            self.listView_runningTasks.setEnabled(False)
        elif choice == ActWhen.SELECTED_TASKS_COMPLETED:
            self.listView_runningTasks.setEnabled(True)
        else:
            raise Exception("Unknown Scheduler actWhen")

    @pyqtSlot()
    def accept(self):
        actWhen = ActWhen(self.comboBox_actWhen.currentData())
        action = Action(self.comboBox_action.currentData())
        app.schedulerModel.set(actWhen, action)
        self.close()
