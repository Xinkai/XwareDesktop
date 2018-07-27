# -*- coding: utf-8 -*-

from models.TaskMapBase import TaskMapBase
from .definitions import Aria2TaskClass
from .item import Aria2TaskItem


def _excludeMetadata(item) -> bool:
    if len(item["files"]) == 1:
        file = item["files"][0]
        if file["path"].startswith("[METADATA]") and len(file["uris"]) == 0:
            return False
    return True


class TaskMap(TaskMapBase):
    _Item = Aria2TaskItem

    def __init__(self, *, klass):
        assert isinstance(klass, Aria2TaskClass)
        super().__init__(klass = klass)

    def updateData(self, updatingList = None):
        # exclude only-metadata entries
        updatingList = list(filter(_excludeMetadata, updatingList))

        updating = dict(zip(
            map(lambda i: "{ns}|{id}".format(ns = self.namespace, id = i["gid"]),
                updatingList),
            updatingList))

        super().updateData(updating)
