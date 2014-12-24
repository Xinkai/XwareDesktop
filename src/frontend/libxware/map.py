# -*- coding: utf-8 -*-

from models.TaskMapBase import TaskMapBase
from .vanilla import TaskClass
from .item import XwareTaskItem


class TaskMap(TaskMapBase):
    _Item = XwareTaskItem

    def __init__(self, *, klass):
        assert isinstance(klass, TaskClass)
        super().__init__(klass = klass)

    def updateData(self, updatingList = None):
        updating = dict(zip(
            map(lambda i: "{ns}|{id}".format(ns = self.namespace, id = i["id"]),
                updatingList),
            updatingList))
        super().updateData(updating)
