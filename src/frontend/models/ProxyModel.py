# -*- coding: utf-8 -*-

from PyQt5.QtCore import pyqtSlot, pyqtSignal, QModelIndex, QSortFilterProxyModel


class ProxyModel(QSortFilterProxyModel):
    srcDataChanged = pyqtSignal(int, int)  # row1, row2

    def __init__(self, parent = None):
        super().__init__(parent)

    @pyqtSlot(QModelIndex, QModelIndex, "QVector<int>")
    def _slotSrcDataChanged(self, topLeft, bottomRight, roles):
        self.srcDataChanged.emit(topLeft.row(), bottomRight.row())

    def setSourceModel(self, model):
        model.dataChanged.connect(self._slotSrcDataChanged)
        super().setSourceModel(model)

    @pyqtSlot(int, result = "QVariantMap")
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
