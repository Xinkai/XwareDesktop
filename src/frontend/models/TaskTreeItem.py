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
        return Qt.Checked if self._selected else Qt.Unchecked

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

    def setData(self, *, size, selected):
        self._size = size
        self._selected = selected

    @property
    def children(self):
        return self._children

    def nthChild(self, i: int):
        return self.children[list(self.children.keys())[i]]

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

    def addSubTask(self, task):
        path0, path1 = self._splitPath(task["name"])
        subTree, created = self.findOrCreateSubtree(path0)

        if created and not path1:
            subTree.setData(size = task["size"],
                            selected = task["selected"])
            self._children[path0] = subTree

        if path1:
            # recursively call addSubTask
            subTask = task.copy()
            subTask["name"] = path1
            subTree.addSubTask(subTask)

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
