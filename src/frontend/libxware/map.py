# -*- coding: utf-8 -*-

from collections import OrderedDict
from .vanilla import TaskState
from .item import XwareTaskItem as Item


_RUNNING_SPEED_SAMPLE_COUNT = 25


class Tasks(OrderedDict):
    """TaskModel underlying data"""

    def __init__(self, adapter, state):
        super().__init__()
        assert isinstance(state, TaskState)
        self.adapter = adapter
        self._state = state

    def updateData(self, updatingList = None):
        updating = dict(zip(
            map(lambda i: "{ns}|{id}".format(ns = self.adapter.namespace, id = i["id"]),
                updatingList),
            updatingList))

        currentKeys = set(self.keys())
        updatingKeys = set(updating.keys())

        addedKeys = updatingKeys - currentKeys
        modifiedKeys = updatingKeys & currentKeys  # Alter/change/modify
        removedKeys = currentKeys - updatingKeys

        for k in modifiedKeys:
            self[k].update(updating[k], self._state)

        for k in addedKeys:
            # Note: __setitem__ is overridden
            self[k] = updating[k]

        for k in removedKeys:
            # Note: __delitem__ is overridden
            del self[k]

    def __setitem__(self, key, value, **kwargs):
        if key in self:
            raise ValueError("__setitem__ is specialized for inserting.")
        ret = self.beforeInsert(key)
        if ret:
            if isinstance(ret, Item):
                item = ret
                item.update(value, self._state)
            else:
                item = Item(adapter = self.adapter)
                item.update(value, self._state)
            super().__setitem__(key, item)
            self.afterInsert()

    def __delitem__(self, key, **kwargs):
        if self.beforeDelete(self.index(key)):
            popped = self[key]
            super().__delitem__(key)
            self.moveToStash(popped)
            self.afterDelete()

    def index(self, key):
        return list(self.keys()).index(key)

    # =========================== FOREIGN DEPENDENCY ===========================
    # When attached to TaskManager, set by it
    def beforeInsert(self, key):
        raise NotImplementedError()

    def afterInsert(self):
        raise NotImplementedError()

    def beforeDelete(self, index):
        raise NotImplementedError()

    def moveToStash(self, item):
        raise NotImplementedError()

    def afterDelete(self):
        raise NotImplementedError()
    # ======================== END OF FOREIGN DEPENDENCY ========================
