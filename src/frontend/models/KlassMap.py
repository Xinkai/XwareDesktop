# -*- coding: utf-8 -*-

import logging
from collections import MutableMapping, namedtuple, OrderedDict
from .TaskMapBase import TaskMapBase

PendingDeletionRecord = namedtuple(
    "PendingDeletion",
    ["fromKlass", "taskMapTicks"]
)


class KlassMap(MutableMapping):
    # a dict-like object that combines tasks from all classes.
    # key: rid   value: taskItem

    def __init__(self, *, adapter: object, namespace: str, taskModel: object):
        self.__namespace = namespace
        self.__adapterMap = None
        self.__adapter = adapter
        self.__taskModel = taskModel

        # taskMaps: {
        #   klass1(int):
        #       taskMap1(dict): {
        #           rid1(str): item1(item),
        #           rid2(str): item2(item),
        #       }
        #   ,
        #   klass2(int):
        #       ...
        #   ,
        # }
        self._taskMaps = OrderedDict()

        # pendingDeletions: {
        #   rid1: [0, 1, 1, 1](ticks),
        # }
        self._pendingDeletions = dict()  # remember when the item is mark stashed

        # {1: 0, 2: 3, 3: 5...}
        self._mapTickCount = OrderedDict()  # increment when a map is updated,
        # useful to really delete items.

    def __len__(self):
        return sum(map(len, self._taskMaps.values()))

    def __getitem__(self, rid: str):
        for taskMap in self._taskMaps.values():
            try:
                return taskMap[rid]
            except KeyError:
                continue
        raise KeyError("Cannot find {key} from KlassMap".format(key = rid))

    def __iter__(self):
        for taskMap in self._taskMaps.values():
            yield from taskMap

    def __delitem__(self, rid: str):
        fromKlass = self.findItemKlass(rid)

        item = self[rid]
        if item.isDeletionPending:
            return
        assert rid not in self._pendingDeletions
        item.isDeletionPending = True
        self._pendingDeletions[rid] = PendingDeletionRecord(
            fromKlass = fromKlass,
            taskMapTicks = list(self._mapTickCount.values()),
        )

    def __setitem__(self, key, value):
        raise NotImplementedError("Must not call __setitem__ on KlassMap.")

    def findItemKlass(self, rid: str) -> "klass":
        for klass in self._taskMaps:
            if rid in self._taskMaps[klass]:
                return klass
        raise KeyError()

    @property
    def namespace(self) -> str:
        return self.__namespace

    def addTaskMap(self, taskMap: TaskMapBase):
        klass = taskMap.klass
        if klass in self._taskMaps:
            raise RuntimeError("Already added.")
        taskMap.namespace = self.namespace
        taskMap.setKlassMap(self)
        taskMap.setTaskModel(self.__taskModel)
        self._mapTickCount[klass] = 0
        self._taskMaps[klass] = taskMap

    def setAdapterMap(self, adapterMap: object):
        self.__adapterMap = adapterMap

    def baseIndexForKlass(self, klass: int) -> int:
        result = 0
        for k in self._taskMaps:
            if k == klass:
                return result
            result += len(self._taskMaps[k])

    def beforeInsert(self, klass: int, rid: str) -> {False: "deferred",
                                                     True: "goahead",
                                                     "item": "moved from another map"}:
        try:
            item = self[rid]
        except KeyError:
            relDstIndex = self.baseIndexForKlass(klass) + len(self._taskMaps[klass])
            self.__adapterMap.beforeInsert(self.namespace, relDstIndex)
            return True

        if not item.isDeletionPending:
            # The item hasn't been marked pending deletion.
            # return False so that the map should skip this one.
            print("deferred", self.namespace, rid)
            return False
        else:
            record = self._pendingDeletions[rid]
            srcKlass = record.fromKlass
            relSrcIndex = self.baseIndexForKlass(srcKlass) + self._taskMaps[srcKlass].index(rid)
            relDstIndex = self.baseIndexForKlass(klass) + len(self._taskMaps[klass])

            if (relSrcIndex == relDstIndex) or (relSrcIndex + 1 == relDstIndex):
                # relSrcIndex == relDstIndex -> Invalid move, prohibited by Qt
                # relSrcIndex + 1 == relDstIndex -> No-op move, also causes problems with Qt
                needMoveRow = False
            else:
                needMoveRow = True

            if needMoveRow:
                # start to move
                self.__adapterMap.beforeMove(self.namespace, relSrcIndex, relDstIndex)

            del self._taskMaps[srcKlass][rid]
            item.isDeletionPending = False
            del self._pendingDeletions[rid]
            self._taskMaps[klass][rid] = item

            if needMoveRow:
                self.__adapterMap.afterMove()
            return item

    def afterInsert(self):
        self.__adapterMap.afterInsert()

    def index(self, rid: str) -> int:
        result = 0
        for taskMap in self._taskMaps.values():
            try:
                result += taskMap.index(rid)
                break
            except ValueError:
                result += len(taskMap)
        else:
            raise ValueError("Cannot be found.")
        return result

    def doneUpdating(self, klass: int):
        self._mapTickCount[klass] += 1
        for rid, record in self._pendingDeletions.copy().items():
            ticks = record.taskMapTicks
            nows = self._mapTickCount.values()

            if not all(map(lambda pair: pair[0] < pair[1], zip(ticks, nows))):
                continue

            relIndex = self.index(rid)
            self.__adapterMap.beginRemoveRows(self.namespace, relIndex)
            del self._taskMaps[record.fromKlass][rid]
            del self._pendingDeletions[rid]
            self.__adapterMap.endRemoveRows()

    def klass(self, klass):
        return self._taskMaps[klass]
