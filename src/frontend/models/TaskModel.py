# -*- coding: utf-8 -*-

from launcher import app

from collections import defaultdict
import enum
from itertools import groupby

from PyQt5.QtCore import QAbstractTableModel, Qt, pyqtSlot, pyqtSignal, QModelIndex, QDateTime
from utils.system import systemOpen, viewOneFile, viewMultipleFiles

from .TaskManager import TaskManager


TaskDataRole = Qt.UserRole + 100
CreationTimeRole = Qt.UserRole + 101
TaskClassRole = Qt.UserRole + 102


@enum.unique
class TaskClass(enum.IntEnum):
    RUNNING = 1
    COMPLETED = 2
    RECYCLED = 4
    FAILED = 8
    INVALID = 16
    ALL = RUNNING | COMPLETED | RECYCLED | FAILED


class TaskModel(QAbstractTableModel):
    sigBeforeInsert = pyqtSignal(int)
    sigAfterInsert = pyqtSignal()
    sigBeforeRemove = pyqtSignal(int)
    sigAfterRemove = pyqtSignal()

    taskCompleted = pyqtSignal("QObject")  # emits from TaskItem

    def __init__(self, parent = None):
        super().__init__(parent)
        self.taskManager = TaskManager(self)

        # TaskManager must not call {begin|end}{Insert|Remove}Rows directly, as it will result in
        # unpredictable data corruption.
        self.sigBeforeInsert.connect(self.slotBeforeInsert, Qt.BlockingQueuedConnection)
        self.sigAfterInsert.connect(self.slotAfterInsert, Qt.BlockingQueuedConnection)
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
        return len(self.roleNames())

    def roleNames(self):
        return {
            Qt.DisplayRole: "display",
            TaskDataRole: "taskData",
            CreationTimeRole: "creationTime",
            TaskClassRole: "taskClass",
        }

    def data(self, qModelIndex, role = None):
        assert qModelIndex.row() >= 0, "row = {}".format(qModelIndex.row())
        if role == TaskDataRole:
            result = self.taskManager.at(qModelIndex.row())
            return result
        elif role == Qt.DisplayRole:
            return self.data(qModelIndex, role = TaskDataRole).name
        elif role == CreationTimeRole:
            dt = QDateTime.fromTime_t(
                self.data(qModelIndex, role = TaskDataRole).creationTime)
            return dt
        elif role == TaskClassRole:
            return self.data(qModelIndex, TaskDataRole).klass

    def get(self, qModelIndex):
        return self.data(qModelIndex, TaskDataRole)

    def flags(self, qModelIndex):
        return Qt.ItemIsSelectable | Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | \
            Qt.ItemNeverHasChildren

    def _sortGroupByAdapter(self, tasks: "list<QModelIndex>") -> "{ns1: [data1, data2]...}":
        tasks = sorted(tasks, key = lambda t: t.row())
        taskDatas = map(self.get, tasks)

        result = defaultdict(list)
        for ns, tasks_ in groupby(taskDatas, key = lambda task: task.namespace):
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

    # =============== The following methods hand taskData directly to the adapter ===============
    def openLixianChannel(self, task: QModelIndex, enable: bool):
        taskItem = self.get(task)
        ns = taskItem.namespace
        assert ns.startswith("xware")
        app.adapterManager.adapter(ns).do_openLixianChannel(taskItem, enable)

    def openVipChannel(self, task: QModelIndex):
        taskItem = self.get(task)
        ns = taskItem.namespace
        assert ns.startswith("xware")
        app.adapterManager.adapter(ns).do_openVipChannel(taskItem)

    # ============================= Adapter-independent operations =============================
    def systemOpen(self, task: QModelIndex):
        taskData = self.get(task)
        systemOpen(taskData.fullpath)

    def viewOneTask(self, task: QModelIndex):
        taskData = self.get(task)
        viewOneFile(taskData.fullpath)

    def viewMultipleTasks(self, tasks: "list<QModelIndex>"):
        taskDatas = map(self.get, tasks)
        fullpaths = map(lambda task: task.fullpath, taskDatas)
        viewMultipleFiles(fullpaths)
