# -*- coding: utf-8 -*-

from collections import OrderedDict
from .vanilla import TaskState


_RUNNING_SPEED_SAMPLE_COUNT = 25


class Tasks(OrderedDict):
    """TaskModel underlying data"""

    def __init__(self, namespace, state):
        super().__init__()
        assert isinstance(state, TaskState)
        self.namespace = namespace
        self._state = state

    def updateData(self, updatingList = None):
        if not updatingList and self._state is TaskState.RUNNING:
            # TODO: push speed 0 to speeds
            pass

        updating = dict(zip(
            map(lambda i: "{ns}|{id}".format(ns = self.namespace, id = i["id"]),
                updatingList),
            updatingList))

        currentKeys = set(self.keys())
        updatingKeys = set(updating.keys())

        addedKeys = updatingKeys - currentKeys
        modifiedKeys = updatingKeys & currentKeys  # Alter/change/modify
        removedKeys = currentKeys - updatingKeys

        # if self._state is TaskState.RUNNING:
        #     # update speeds for running tasks
        #
        #     for updatingKey in updatingKeys:
        #         speeds = self._getSpeeds(updatingKey)
        #         try:
        #             speed = updating[updatingKey]["speed"]
        #         except KeyError:
        #             speed = 0
        #
        #         speeds = self._composeNewSpeeds(speeds, speed)
        #         updating[updatingKey]["speeds"] = speeds

        if modifiedKeys:
            if self._state == TaskState.RUNNING:
                # modify everything at once
                self.beforeModify()
                super(OrderedDict, self).update({key: updating[key] for key in modifiedKeys})
                self.afterModify(0, len(modifiedKeys))

        if addedKeys:
            # add them one by one
            for k in addedKeys:
                # Note: __setitem__ is overridden
                self[k] = updating[k]

        # # remove removedKeys
        if removedKeys:
            for k in removedKeys:
                # Note: __delitem__ is overridden
                del self[k]

    @staticmethod
    def _composeNewSpeeds(oldSpeeds, newSpeed):
        return oldSpeeds[1:] + [newSpeed]

    def _getSpeeds(self, key):
        try:
            result = self[key]["speeds"]
        except KeyError:
            result = [0] * _RUNNING_SPEED_SAMPLE_COUNT
        return result

    def __setitem__(self, key, value, **kwargs):
        if key in self:
            raise ValueError("__setitem__ is specialized for inserting.")
        goahead = self.beforeInsert(key)
        if goahead:
            super().__setitem__(key, value)
            self.afterInsert()

    def __delitem__(self, key, **kwargs):
        if self.beforeDelete(self.index(key)):
            super().__delitem__(key)
            self.afterDelete()

    def index(self, key):
        return list(self.keys()).index(key)

    # =========================== FOREIGN DEPENDENCY ===========================
    # When attached to TaskManager, set by it
    def beforeInsert(self, key):
        raise NotImplementedError()

    def afterInsert(self):
        raise NotImplementedError()

    def beforeModify(self):
        raise NotImplementedError()

    def afterModify(self, index0, index1):
        raise NotImplementedError()

    def beforeDelete(self, index):
        raise NotImplementedError()

    def afterDelete(self):
        raise NotImplementedError()
    # ======================== END OF FOREIGN DEPENDENCY ========================
