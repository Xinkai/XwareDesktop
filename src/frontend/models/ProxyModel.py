# -*- coding: utf-8 -*-

from PyQt5.QtCore import pyqtSlot, pyqtSignal, QModelIndex, QSortFilterProxyModel, Qt, Q_ENUMS, \
    pyqtProperty

try:  # TODO: when QML ships ,remove this!
    from PyQt5.QtQml import qmlRegisterUncreatableType
except ImportError:
    qmlRegisterUncreatableType = None

from utils.misc import dropPy34Enum
from .TaskModel import CreationTimeRole, TaskClass, TaskClassRole, TaskState
from libxware.definitions import VipChannelState, LixianChannelState


class ProxyModel(QSortFilterProxyModel):
    srcDataChanged = pyqtSignal(int, int)  # row1, row2
    taskClassFilterChanged = pyqtSignal()

    def __init__(self, parent = None):
        super().__init__(parent)
        self.setDynamicSortFilter(True)
        self.sort(0, Qt.DescendingOrder)
        self.setFilterCaseSensitivity(False)
        self._taskClassFilter = TaskClass.RUNNING

    @pyqtProperty(int, notify = taskClassFilterChanged)
    def taskClassFilter(self):
        return self._taskClassFilter

    @taskClassFilter.setter
    def taskClassFilter(self, value):
        if value != self._taskClassFilter:
            self._taskClassFilter = value
            self.taskClassFilterChanged.emit()
            self.invalidateFilter()

    def filterAcceptsRow(self, srcRow: int, srcParent: QModelIndex):
        result = super().filterAcceptsRow(srcRow, srcParent)
        if result:
            srcModel = self.sourceModel()
            klass = srcModel.data(srcModel.index(srcRow, 0), TaskClassRole)
            if klass & self.taskClassFilter:
                return True
            else:
                return False

        return result

    @pyqtSlot(QModelIndex, QModelIndex, "QVector<int>")
    def _slotSrcDataChanged(self, topLeft, bottomRight, roles):
        self.srcDataChanged.emit(topLeft.row(), bottomRight.row())

    def setSourceModel(self, model):
        model.dataChanged.connect(self._slotSrcDataChanged)
        super().setSourceModel(model)
        self.setSortRole(CreationTimeRole)

    @pyqtSlot(int, result = "QVariant")
    def get(self, i: int):
        index = self.mapToSource(self.index(i, 0))
        return self.sourceModel().get(index)

    def _getModelIndex(self, rowId):
        return self.index(rowId, 0)

    def _getSourceModelIndex(self, rowId):
        return self.mapToSource(self._getModelIndex(rowId))

    def _getModelIndice(self, rowIds):
        return map(lambda row: self.index(row, 0), rowIds)

    def _getSourceModelIndice(self, rowIds):
        return map(self.mapToSource, self._getModelIndice(rowIds))

    @pyqtSlot(str, result = "void")
    def setNameFilter(self, name):
        if name:
            self.setFilterFixedString(name)
        else:
            self.setFilterFixedString(None)

    @pyqtSlot("QVariantMap", result = "void")
    def pauseTasks(self, options):
        srcIndice = list(self._getSourceModelIndice(options["rows"]))
        self.sourceModel().pauseTasks(srcIndice, options)

    @pyqtSlot("QVariantMap", result = "void")
    def startTasks(self, options):
        srcIndice = list(self._getSourceModelIndice(options["rows"]))
        self.sourceModel().startTasks(srcIndice, options)

    @pyqtSlot(int, result = "void")
    def systemOpen(self, rowId):
        srcIndex = self._getSourceModelIndex(rowId)
        self.sourceModel().systemOpen(srcIndex)

    @pyqtSlot(int, bool, result = "void")
    def openLixianChannel(self, rowId, enable: bool):
        srcIndex = self._getSourceModelIndex(rowId)
        self.sourceModel().openLixianChannel(srcIndex, enable)

    @pyqtSlot(int, result = "void")
    def openVipChannel(self, rowId):
        srcIndex = self._getSourceModelIndex(rowId)
        self.sourceModel().openVipChannel(srcIndex)

    @pyqtSlot(int, result = "void")
    def viewOneTask(self, rowId):
        srcIndex = self._getSourceModelIndex(rowId)
        self.sourceModel().viewOneTask(srcIndex)

    @pyqtSlot("QList<int>", result = "void")
    def viewMultipleTasks(self, rowIds):
        srcIndice = list(self._getSourceModelIndice(rowIds))
        self.sourceModel().viewMultipleTasks(srcIndice)

    # put this at the end of the class, to workaround a PyQt bug
    # See # 97
    Q_ENUMS(dropPy34Enum(TaskClass, "Class"))
    Q_ENUMS(dropPy34Enum(TaskState, "State"))
    Q_ENUMS(dropPy34Enum(LixianChannelState, "Lixian"))
    Q_ENUMS(dropPy34Enum(VipChannelState, "Vip"))

if qmlRegisterUncreatableType:
    qmlRegisterUncreatableType(ProxyModel, 'TaskModel', 1, 0, 'TaskModel',
                               "TaskModel cannot be created.")
