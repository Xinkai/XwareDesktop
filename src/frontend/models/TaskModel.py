# -*- coding: utf-8 -*-

from collections import defaultdict
import enum
from itertools import groupby

from PyQt5.QtCore import QAbstractListModel, Qt, pyqtSlot, pyqtSignal, QModelIndex, QDateTime
from utils.system import systemOpen, viewOneFile, viewMultipleFiles

from .AdapterMap import AdapterMap


TaskDataRole = Qt.UserRole + 100
CreationTimeRole = Qt.UserRole + 101
TaskClassRole = Qt.UserRole + 102


@enum.unique
class TaskClass(enum.IntEnum):
    RUNNING = 1  # state: downloading, waiting, paused
    COMPLETED = 2  # state: completed
    RECYCLED = 4
    FAILED = 8
    INVALID = 16
    ALL = RUNNING | COMPLETED | RECYCLED | FAILED


@enum.unique
class TaskState(enum.IntEnum):
    Downloading = 0  # Downloading; seeding doesn't count
    Waiting = 1
    Paused = 2
    Completed = 3  # Downloading finished; doesn't care about seeding or not
    Removed = 4  # Deleted/moved from the file system
    Failed = 5
    Unrecognized = 99


class TaskModel(QAbstractListModel):
    sigBeforeInsert = pyqtSignal(int)
    sigAfterInsert = pyqtSignal()
    sigBeforeRemove = pyqtSignal(int)
    sigAfterRemove = pyqtSignal()
    sigBeforeMove = pyqtSignal(int, int)
    sigAfterMove = pyqtSignal()

    taskCompleted = pyqtSignal("QObject")  # emits from TaskItem

    def __init__(self, parent = None):
        super().__init__(parent)
        self.adapterMap = AdapterMap(self)
        self.__adapterManager = None

        # TaskManager must not call {begin|end}{Insert|Remove}Rows directly, as it will result in
        # unpredictable data corruption.
        self.sigBeforeInsert.connect(self.slotBeforeInsert, Qt.BlockingQueuedConnection)
        self.sigAfterInsert.connect(self.slotAfterInsert, Qt.BlockingQueuedConnection)
        self.sigBeforeRemove.connect(self.slotBeforeRemove, Qt.BlockingQueuedConnection)
        self.sigAfterRemove.connect(self.slotAfterRemove, Qt.BlockingQueuedConnection)
        self.sigBeforeMove.connect(self.slotBeforeMove, Qt.BlockingQueuedConnection)
        self.sigAfterMove.connect(self.slotAfterMove, Qt.BlockingQueuedConnection)

    def setAdapterManager(self, adapterManager):
        self.__adapterManager = adapterManager

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

    @pyqtSlot(int, int)
    def slotBeforeMove(self, src: int, dst: int):
        ok = self.beginMoveRows(QModelIndex(), src, src, QModelIndex(), dst)
        if not ok:
            raise RuntimeError("beginMoveRows", src, dst)

    @pyqtSlot()
    def slotAfterMove(self):
        self.endMoveRows()

    def rowCount(self, qModelIndex=None, *args, **kwargs):
        return len(self.adapterMap)

    def columnCount(self, *args, **kwargs):
        return len(self.roleNames())

    def roleNames(self):
        return {
            Qt.DisplayRole: b"display",
            TaskDataRole: b"taskData",
            CreationTimeRole: b"creationTime",
            TaskClassRole: b"taskClass",
            TaskClassRole: b"taskClass",
        }

    def data(self, qModelIndex: QModelIndex, role = None):
        if not qModelIndex.row() >= 0:
            raise RuntimeError("row = {}".format(qModelIndex.row()))

        if role == TaskDataRole:
            result = self.adapterMap.at(qModelIndex.row())
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
            self.__adapterManager.adapter(ns).do_pauseTasks(taskDatas, options)

    def startTasks(self, tasks: "list<QModelIndex>", options):
        for ns, taskDatas in self._sortGroupByAdapter(tasks).items():
            self.__adapterManager.adapter(ns).do_startTasks(taskDatas, options)

    def delTasks(self, tasks: "list<QModelIndex>", options):
        for ns, taskDatas in self._sortGroupByAdapter(tasks).items():
            self.__adapterManager.adapter(ns).do_delTasks(taskDatas, options)

    def restoreTasks(self, tasks: "list<QModelIndex>", options):
        for ns, taskDatas in self._sortGroupByAdapter(tasks).items():
            self.__adapterManager.adapter(ns).do_restoreTasks(taskDatas, options)

    # =============== The following methods hand taskData directly to the adapter ===============
    def openLixianChannel(self, task: QModelIndex, enable: bool):
        taskItem = self.get(task)
        ns = taskItem.namespace
        assert ns.startswith("xware")
        self.__adapterManager.adapter(ns).do_openLixianChannel(taskItem, enable)

    def openVipChannel(self, task: QModelIndex):
        taskItem = self.get(task)
        ns = taskItem.namespace
        assert ns.startswith("xware")
        self.__adapterManager.adapter(ns).do_openVipChannel(taskItem)

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
