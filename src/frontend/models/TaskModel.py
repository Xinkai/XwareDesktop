# -*- coding: utf-8 -*-

from launcher import app

from collections import defaultdict
from itertools import groupby

from PyQt5.QtCore import QAbstractListModel, Qt, pyqtSlot, pyqtSignal, QModelIndex
from .TaskManager import TaskManager


TaskDataRole = Qt.UserRole + 100


class TaskModel(QAbstractListModel):
    sigBeforeInsert = pyqtSignal(int)
    sigAfterInsert = pyqtSignal()
    sigBeforeModify = pyqtSignal()
    sigAfterModify = pyqtSignal(int, int)  # allow modify range
    sigBeforeRemove = pyqtSignal(int)
    sigAfterRemove = pyqtSignal()

    def __init__(self, parent = None):
        super().__init__(parent)
        self.taskManager = TaskManager(self)

        # TaskManager must not call {begin|end}{Insert|Remove}Rows directly, as it will result in
        # unpredictable data corruption.
        self.sigBeforeInsert.connect(self.slotBeforeInsert, Qt.BlockingQueuedConnection)
        self.sigAfterInsert.connect(self.slotAfterInsert, Qt.BlockingQueuedConnection)
        self.sigBeforeModify.connect(self.slotBeforeModify, Qt.BlockingQueuedConnection)
        self.sigAfterModify.connect(self.slotAfterModify, Qt.BlockingQueuedConnection)
        self.sigBeforeRemove.connect(self.slotBeforeRemove, Qt.BlockingQueuedConnection)
        self.sigAfterRemove.connect(self.slotAfterRemove, Qt.BlockingQueuedConnection)

    @pyqtSlot(int)
    def slotBeforeInsert(self, i):
        # doesn't support range insertion, because individual map has no idea whether the item will
        # be inserted or delayed.
        self.beginInsertRows(QModelIndex(), i, i)

    @pyqtSlot()
    def slotAfterInsert(self):
        self.endInsertRows()

    @pyqtSlot()
    def slotBeforeModify(self):
        raise NotImplementedError()

    @pyqtSlot(int, int)
    def slotAfterModify(self, i0, i1):
        self.dataChanged.emit(self.index(i0),
                              self.index(i1),
                              [TaskDataRole])

    @pyqtSlot(int)
    def slotBeforeRemove(self, i):
        # because it's very like that removed items are not continuous, doesn't support range
        self.beginRemoveRows(QModelIndex(), i, i)

    @pyqtSlot()
    def slotAfterRemove(self):
        self.endRemoveRows()

    def rowCount(self, qModelIndex=None, *args, **kwargs):
        return len(self.taskManager)

    def columnCount(self, *args, **kwargs):
        raise NotImplementedError()

    def roleNames(self):
        return {
            Qt.DisplayRole: "display",
            TaskDataRole: "taskData",
        }

    def data(self, qModelIndex, role = None):
        # assert role == Qt.DisplayRole, "data(role={})".format(role)
        assert qModelIndex.row() >= 0, "row = {}".format(qModelIndex.row())
        if role == TaskDataRole:
            # self._lock.acquire()
            result = self.taskManager.at(qModelIndex.row())
            # self._lock.release()
            return result
        elif role == Qt.DisplayRole:
            return self.data(qModelIndex, role = TaskDataRole)["name"]

    def get(self, qModelIndex):
        return self.data(qModelIndex, TaskDataRole)

    def flags(self, qModelIndex):
        return Qt.ItemIsSelectable | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | \
            Qt.ItemNeverHasChildren

    def _sortGroupByAdapter(self, tasks: "list<QModelIndex>") -> "{ns1: [data1, data2]...}":
        tasks = sorted(tasks, key = lambda t: t.row())
        taskDatas = map(self.get, tasks)

        result = defaultdict(list)
        for ns, tasks_ in groupby(taskDatas, key = lambda task: task["ns"]):
            for task_ in tasks_:
                result[ns].append(task_)
        return result

    # ====== The following methods support bulk operation, hand tasks to the adapter ======
    def pauseTasks(self, tasks: "list<QModelIndex>", options):
        for ns, taskDatas in self._sortGroupByAdapter(tasks).items():
            app.adapterManager.adapter(ns).do_pauseTasks(taskDatas, options)

    def startTasks(self, tasks: "list<QModelIndex>", options):
        for ns, taskDatas in self._sortGroupByAdapter(tasks).items():
            app.adapterManager.adapter(ns).do_startTasks(taskDatas, options)

    def viewMultipleTasks(self, tasks: "list<QModelIndex>"):
        for ns, taskDatas in self._sortGroupByAdapter(tasks).items():
            app.adapterManager.adapter(ns).do_viewMultipleTasks(taskDatas)

    # =============== The following methods hand taskData directly to the adapter ===============
    def systemOpen(self, task: QModelIndex):
        taskData = self.get(task)
        ns = taskData["ns"]
        app.adapterManager.adapter(ns).do_systemOpen(taskData)

    def viewOneTask(self, task: QModelIndex):
        taskData = self.get(task)
        ns = taskData["ns"]
        app.adapterManager.adapter(ns).do_viewOneTask(taskData)

    def openLixianChannel(self, task: QModelIndex, enable: bool):
        taskData = self.get(task)
        ns = taskData["ns"]
        assert ns.startswith("xware")
        app.adapterManager.adapter(ns).do_openLixianChannel(taskData, enable)

    def openVipChannel(self, task: QModelIndex):
        taskData = self.get(task)
        ns = taskData["ns"]
        assert ns.startswith("xware")
        app.adapterManager.adapter(ns).do_openVipChannel(taskData)
