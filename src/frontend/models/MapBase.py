# -*- coding: utf-8 -*-

from collections import OrderedDict
import threading


class TaskMapBase(OrderedDict):
    """TaskModel underlying data"""
    _Lock = threading.Lock()
    _Item = None  # "the class with which new task item can be created"

    def __init__(self,
                 adapter: "instance of the adapter",
                 klass: "this map is used for this kind of map, native to the adapter"):
        super().__init__()
        self.adapter = adapter
        self._klass = klass

    def _updateDict(self, updating: dict = None):
        with self.__class__._Lock:
            currentKeys = set(self.keys())
            updatingKeys = set(updating.keys())

            addedKeys = updatingKeys - currentKeys
            modifiedKeys = updatingKeys & currentKeys  # Alter/change/modify
            removedKeys = currentKeys - updatingKeys

            for k in modifiedKeys:
                self[k].update(updating[k], self._klass)

            for k in addedKeys:
                self.insert(k, updating[k])

            for k in removedKeys:
                self.markPendingDeletion(k)
            self.doneUpdating()

    def insert(self, key, value):
        ret = self.beforeInsert(key)
        if ret is True:
            item = self.__class__._Item(adapter = self.adapter)
            item.update(value, self._klass)
            self[key] = item
            self.afterInsert()
        elif isinstance(ret, self.__class__._Item):
            assert key in self
            item = ret
            item.update(value, self._klass)
        elif ret is False:
            pass

    def index(self, key):
        return list(self.keys()).index(key)

    # =========================== FOREIGN DEPENDENCY ===========================
    # When attached to TaskManager, set by it
    def beforeInsert(self, key):
        raise NotImplementedError()

    def afterInsert(self):
        raise NotImplementedError()

    def markPendingDeletion(self, key):
        raise NotImplementedError()

    def doneUpdating(self):
        raise NotImplementedError()
    # ======================== END OF FOREIGN DEPENDENCY ========================
