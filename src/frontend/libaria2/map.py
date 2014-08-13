# -*- coding: utf-8 -*-

from models.MapBase import TaskMapBase
from .definitions import Aria2TaskClass
from .item import Aria2TaskItem


class TaskMap(TaskMapBase):
    _Item = Aria2TaskItem

    def __init__(self, adapter, klass):
        assert isinstance(klass, Aria2TaskClass)
        super().__init__(adapter, klass)

    def updateData(self, updatingList = None):
        updating = dict(zip(
            map(lambda i: "{ns}|{id}".format(ns = self.adapter.namespace, id = i["gid"]),
                updatingList),
            updatingList))
        self._updateDict(updating)
