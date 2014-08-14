# -*- coding: utf-8 -*-

from models.MapBase import TaskMapBase
from .definitions import Aria2TaskClass
from .item import Aria2TaskItem


def _excludeMetadata(item) -> bool:
    bittorrent = item.get("bittorrent")
    if bittorrent:
        if "info" not in bittorrent:
            assert len(item["files"]) == 1
            assert item["files"][0]["path"].startswith("[METADATA]")
            return False
    return True


class TaskMap(TaskMapBase):
    _Item = Aria2TaskItem

    def __init__(self, adapter, klass):
        assert isinstance(klass, Aria2TaskClass)
        super().__init__(adapter, klass)

    def updateData(self, updatingList = None):
        # exclude only-metadata entries
        updatingList = list(filter(_excludeMetadata, updatingList))

        updating = dict(zip(
            map(lambda i: "{ns}|{id}".format(ns = self.adapter.namespace, id = i["gid"]),
                updatingList),
            updatingList))

        self._updateDict(updating)
