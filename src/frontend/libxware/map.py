# -*- coding: utf-8 -*-

from models.MapBase import TaskMapBase
from .vanilla import TaskClass
from .item import XwareTaskItem


class TaskMap(TaskMapBase):
    _Item = XwareTaskItem

    def __init__(self, adapter, klass):
        assert isinstance(klass, TaskClass)
        super().__init__(adapter, klass)

    def updateData(self, updatingList = None):
        updating = dict(zip(
            map(lambda i: "{ns}|{id}".format(ns = self.adapter.namespace, id = i["id"]),
                updatingList),
            updatingList))
        self._updateDict(updating)
