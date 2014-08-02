# -*- coding: utf-8 -*-

import logging
from launcher import app

from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtWidgets import QDialog, QListWidgetItem

from legacy.ui_scheduler import Ui_Dialog
import Schedule


class SchedulerWindow(QDialog, Ui_Dialog):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setupUi(self)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.loadFromScheduler()

    def loadFromScheduler(self):
        # actWhen ComboBox
        for row, pair in enumerate(app.scheduler.POSSIBLE_ACTWHENS):
            self.comboBox_actWhen.addItem(pair[1])
            self.comboBox_actWhen.setItemData(row, pair[0])

        self.slotActWhenChanged(app.scheduler.actWhen)
        self.comboBox_actWhen.setCurrentIndex(app.scheduler.actWhen)
        self.comboBox_actWhen.activated[int].connect(self.slotActWhenChanged)

        # tasks list
        runningTasks = app.etmpy.runningTasksStat.getTasks()
        waitingTaskIds = app.scheduler.waitingTaskIds
        for rTaskId, rTask in runningTasks.items():
            item = QListWidgetItem(rTask["name"])
            item.setData(Qt.UserRole, rTaskId)
            self.listWidget_tasks.addItem(item)

            # must be set before being added
            if rTaskId in waitingTaskIds:
                item.setSelected(True)
            else:
                item.setSelected(False)

        # action comboBox
        selectedIndex = None
        for action in app.scheduler.actions:
            if action.command or action.availability == "yes":
                self.comboBox_action.addItem(action.displayName)
                row = self.comboBox_action.count() - 1
                self.comboBox_action.setItemData(row, action.actionId)
                if app.scheduler.actionId == action.actionId:
                    selectedIndex = row
        self.comboBox_action.setCurrentIndex(selectedIndex)

    @pyqtSlot(int)
    def slotActWhenChanged(self, choice):
        if choice == Schedule.ALL_TASKS_COMPLETED:
            self.listWidget_tasks.setEnabled(False)
        elif choice == Schedule.SELECTED_TASKS_COMPLETED:
            self.listWidget_tasks.setEnabled(True)
        else:
            raise Exception("Unknown Scheduler actWhen")

    @pyqtSlot()
    def accept(self):
        actWhen = self.comboBox_actWhen.currentData()
        taskIds = set(map(lambda item: item.data(Qt.UserRole),
                          self.listWidget_tasks.selectedItems()))
        actionId = self.comboBox_action.currentData()

        app.scheduler.set(actWhen, taskIds, actionId)
        self.close()
