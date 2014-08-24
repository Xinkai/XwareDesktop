# -*- coding: utf-8 -*-

from collections import OrderedDict
from enum import IntEnum, unique

from PyQt5.QtCore import Qt


@unique
class TaskTreeColumn(IntEnum):
    FileName = 0
    FileSize = 1


class TaskTreeItem(object):
    def __init__(self, parent = None):
        self._parent = parent
        self._children = OrderedDict()
        self._selected = False
        self._name = "UNKNOWN"
        self._size = 0
        self._index = -1

    @property
    def ancestryTree(self):
        if self.isRoot():
            return "ROOT"
        return self.parent.ancestryTree + "/" + self._name

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def size(self):
        if self._children:
            return sum(map(lambda child: child.size, self._children.values()))
        else:
            return self._size

    @property
    def selected(self):
        if self._children:
            states = [node.selected for node in self._children.values()]
            if set(states) == {Qt.Checked}:
                return Qt.Checked
            elif set(states) == {Qt.Unchecked}:
                return Qt.Unchecked
            else:
                return Qt.PartiallyChecked
        else:
            return Qt.Checked if self._selected else Qt.Unchecked

    @selected.setter
    def selected(self, value: bool):
        self._selected = value

    def isRoot(self) -> bool:
        return not bool(self.parent)

    @property
    def parent(self):
        return self._parent

    @property
    def siblings(self):
        p = self._parent
        if p:
            return p.children

    def setData(self, *, size, index, selected):
        self._size = size
        self._index = index
        self._selected = selected

    @property
    def children(self):
        return self._children

    def nthChild(self, i: int):
        return self.children[list(self._children.keys())[i]]

    def siblingNumber(self):
        result = list(self.siblings.values()).index(self)
        return result

    def data(self, column):
        if column == TaskTreeColumn.FileName:
            return self.name

        elif column == TaskTreeColumn.FileSize:
            return self.size

    def childrenCount(self):
        return len(self._children)

    def addSubTask(self, *, name: str, size: int, index: int, selected: bool):
        path0, path1 = self._splitPath(name)
        subTree, created = self.findOrCreateSubtree(path0)

        if created and not path1:
            subTree.setData(size = size,
                            index = index,
                            selected = selected)
            self._children[path0] = subTree

        if path1:
            # recursively call addSubTask
            subTree.addSubTask(name = path1,
                               size = size,
                               index = index,
                               selected = selected)

    def findOrCreateSubtree(self, name):
        try:
            result = self._children[name]
            return result, False
        except KeyError:
            subTree = TaskTreeItem(self)
            subTree.name = name
            self._children[name] = subTree
            return subTree, True

    @staticmethod
    def _splitPath(src: "path/to/the/file") -> ("path" or "file", "to/the/file" or None):
        try:
            i = src.index("/")
            return src[:i], src[i + 1:]
        except ValueError:
            # no path
            return src, None

    def __repr__(self):
        return "{cls}<{ancestryTree}:{contents}>".format(
            cls = self.__class__.__name__,
            ancestryTree = self.ancestryTree,
            contents = len(self._children))
