# -*- coding: utf-8 -*-


from PyQt5.QtCore import pyqtSlot, pyqtSignal, QModelIndex, QSortFilterProxyModel, Qt, Q_ENUMS

from models.TaskModel import CreationTimeRole, TaskClass, TaskClassRole


class SchedulerModel(QSortFilterProxyModel):
    srcDataChanged = pyqtSignal(int, int)  # row1, row2

    def __init__(self, parent = None):
        super().__init__(parent)
        self.setDynamicSortFilter(True)
        self.sort(0, Qt.DescendingOrder)
        self.setFilterCaseSensitivity(False)
        self._taskClassFilter = TaskClass.RUNNING

    def filterAcceptsRow(self, srcRow: int, srcParent: QModelIndex):
        result = super().filterAcceptsRow(srcRow, srcParent)
        if result:
            srcModel = self.sourceModel()
            klass = srcModel.data(srcModel.index(srcRow, 0), TaskClassRole)
            if klass == TaskClass.RUNNING:
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
