# -*- coding: utf-8 -*-


from PyQt5.QtCore import pyqtSlot, QModelIndex, QSortFilterProxyModel, Qt, pyqtSignal, \
    pyqtProperty, QItemSelectionModel

import sys
from models.TaskModel import CreationTimeRole, TaskClass, TaskClassRole

from . import Action, ActWhen
if sys.platform == "win32":
    from .Win32PowerAction import Win32PowerActionManager as PowerActionManager
elif sys.platform == "linux":
    from .PowerAction import PowerActionManager

from .SchedulerCountdown import CountdownMessageBox


class TaskSelectionModel(QItemSelectionModel):
    def __init__(self, model, parent):
        super().__init__(model, parent)


class SchedulerModel(QSortFilterProxyModel):
    schedulerSummaryChanged = pyqtSignal()
    countdownConfirmed = pyqtSignal(bool)

    def __init__(self, parent = None):
        super().__init__(parent)
        self.setDynamicSortFilter(True)
        self.sort(0, Qt.DescendingOrder)
        self.setFilterCaseSensitivity(False)
        self._taskClassFilter = TaskClass.RUNNING

        self.countdownConfirmed[bool].connect(self.confirmed)

        self._action = None
        self._actWhen = None
        self._confirmDlg = None
        self.selectionModel = TaskSelectionModel(self, self)
        self.reset()

        self.powerActionManager = PowerActionManager(self)
        self.rowsInserted.connect(self.mayAct)
        self.rowsRemoved.connect(self.mayAct)

    @property
    def actions(self):
        return self.powerActionManager.actions

    def filterAcceptsRow(self, srcRow: int, srcParent: QModelIndex):
        srcModel = self.sourceModel()
        klass = srcModel.data(srcModel.index(srcRow, 0), TaskClassRole)
        if klass == TaskClass.RUNNING:
            return True
        else:
            return False

    def setSourceModel(self, model):
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

    @pyqtProperty(int, notify = schedulerSummaryChanged)
    def action(self):
        return self._action

    @pyqtProperty(int, notify = schedulerSummaryChanged)
    def actWhen(self):
        return self._actWhen

    def set(self, actWhen, action):
        self._actWhen = actWhen
        self._action = action
        self.mayAct()

    @pyqtProperty(int, notify = schedulerSummaryChanged)
    def blockingTaskCount(self):
        if self.actWhen == ActWhen.ALL_TASKS_COMPLETED:
            return self.rowCount()
        else:
            result = len(self.selectionModel.selectedIndexes())
            return result

    @pyqtSlot()
    def mayAct(self):
        self.schedulerSummaryChanged.emit()
        if self.action == Action.Null:
            return

        if not self.blockingTaskCount:
            self._confirmDlg = CountdownMessageBox(self.action, self)
            self._confirmDlg.show()
            self._confirmDlg.activateWindow()
            self._confirmDlg.raise_()

    # ======================== Confirm Dialog ========================
    # Maybe move out of the model in the future?
    @pyqtSlot(bool)
    def confirmed(self, accepted):
        if accepted:
            self.powerActionManager.act(self.action)
            self.reset()
        else:
            self.reset()

    def reset(self):
        self.set(ActWhen.ALL_TASKS_COMPLETED, Action.Null)
        if self._confirmDlg:
            self._confirmDlg.destroy()
            self._confirmDlg = None
        self.selectionModel.clearSelection()
