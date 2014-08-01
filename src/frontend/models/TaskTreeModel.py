# -*- coding: utf-8 -*-

from .TaskTreeItem import TaskTreeColumn
from PyQt5.QtCore import QAbstractItemModel, QModelIndex, Qt


class TaskTreeModel(QAbstractItemModel):
    def __init__(self, parent = None):
        super().__init__(parent)
        self._root = None

    def setRoot(self, root):
        self._root = root

    def headerData(self, section: int, orientation: "Qt.Orientation", role: int = None):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section == TaskTreeColumn.FileName:
                return "文件名"
            elif section == TaskTreeColumn.FileSize:
                return "大小"
            else:
                raise ValueError()

    def columnCount(self, parent: QModelIndex = None, *args, **kwargs):
        return 2  # filename, filesize

    def rowCount(self, parent: QModelIndex = None, *args, **kwargs):
        if parent.isValid():
            parentItem = parent.internalPointer()
            return parentItem.childrenCount()
        else:
            return self._root.childrenCount()

    def _indexToItem(self, index: QModelIndex):
        if not index.isValid():
            return self._root
        else:
            return index.internalPointer()

    def data(self, index: QModelIndex, role = None):
        if not index.isValid():
            return None

        item = index.internalPointer()
        if role == Qt.DisplayRole:
            return item.data(index.column())
        elif role == Qt.CheckStateRole and index.column() == TaskTreeColumn.FileName:
            return item.selected
        elif role == Qt.DecorationRole and index.column() == TaskTreeColumn.FileName:
            # TODO: use with real icons
            from PyQt5.QtGui import QIcon
            return QIcon.fromTheme("xware-desktop")

        return None

    def flags(self, index: QModelIndex):
        return Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsTristate

    def index(self, row: int, column: int, parent: QModelIndex = None):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        parentItem = self._indexToItem(parent)
        childItem = parentItem.nthChild(row)

        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QModelIndex()

    def parent(self, index: QModelIndex = None):
        if not index.isValid():
            return QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent

        if parentItem == self._root:
            return QModelIndex()
        else:
            return self.createIndex(parentItem.siblingNumber(), 0, parentItem)
