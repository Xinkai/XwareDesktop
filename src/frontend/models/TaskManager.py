# -*- coding: utf-8 -*-

import collections
from functools import partial
from itertools import islice

from PyQt5.QtCore import QModelIndex


PendingDeletionRecord = collections.namedtuple(
    "PendingDeletion",
    ["fromMap", "mapTicks"]
)


class TaskManager(collections.MutableMapping):
    def __init__(self, model):
        self._mapNamespaces = collections.defaultdict(list)  # {"xware-0123": [0, 1, 2, 3], ...}
        self._reversedMapNamespaces = dict()

        # {"xware-legacy|1": [0,1,1,1]}
        # remember when the item is mark stashed
        self._pendingDeletions = dict()

        # {1: 0, 2: 3, 3: 5...}
        # increment when a map is updated, useful to clean stash
        self._mapTickCount = dict()
        self._maps = []
        self._model = model

    # Disable some methods that are expected in a dict.
    def __setitem__(self, key, value):
        raise NotImplementedError()

    def __delitem__(self, key):
        raise NotImplementedError()

    def copy(self):
        raise NotImplementedError()

    def keys(self):
        raise NotImplementedError()

    def values(self):
        raise NotImplementedError()

    def items(self):
        for taskId in self:
            try:
                item = self[taskId]
            except KeyError:
                continue
            yield (taskId, item)

    def __getitem__(self, key):
        # faster than ChainMap's implementation
        ns = key.split("|")[0]
        for nsmap in self._mapsForNamespace(ns):
            try:
                result = nsmap[key]
                return result
            except KeyError:
                pass
        raise KeyError("key {} cannot be found.".format(key))

    def __iter__(self):
        # gives an iterator of TaskIds
        for map_ in self._maps:
            yield from map_

    def __len__(self):
        return sum(map(len, self._maps))

    def __contains__(self, key: str):
        # faster than ChainMap's implementation
        ns = key.split("|")[0]
        return any(key in nsmap for nsmap in self._mapsForNamespace(ns))

    # Custom implementation
    def _mapsForNamespace(self, ns: str):
        return (self._maps[mapId] for mapId in self._mapNamespaces[ns])

    def _baseIndexForMap(self, mapId):
        assert mapId <= len(self._maps)
        return sum(map(len, self._maps[:mapId]))

    def at(self, index: "uint"):
        assert index >= 0, "index = {}".format(index)
        for mapId in range(len(self._maps)):
            mapLIndex = self._baseIndexForMap(mapId)
            mapRIndex = mapLIndex + len(self._maps[mapId]) - 1
            if mapRIndex >= index:
                inmapIndex = index - mapLIndex
                itr = islice(self._maps[mapId].values(), inmapIndex, inmapIndex + 1)
                result = next(itr)
                return result
        raise IndexError("Out of range: index({})".format(index))

    def appendMap(self, map_):
        # All tasks from all backends live in a same chainmap, therefore id needs to be prefixed

        if not isinstance(map_, collections.OrderedDict):
            raise ValueError("Can only register OrderedDict")

        namespace = getattr(map_, "adapter").namespace
        if not namespace:
            raise ValueError("Map must have a namespace property")

        assert not bool(map_), "Map must be empty before registering"

        mapId = len(self._maps)

        # implement map's model related methods
        map_.beforeInsert = partial(self.beforeInsert, mapId)
        map_.afterInsert = self.afterInsert
        map_.markPendingDeletion = partial(self.markPendingDeletion, mapId)
        map_.doneUpdating = partial(self.doneUpdating, mapId)
        self._maps.append(map_)

        self._mapNamespaces[namespace].append(mapId)
        self._reversedMapNamespaces[mapId] = namespace
        self._mapTickCount[mapId] = 0
        return mapId

    def beforeInsert(self, mapId, key) -> {False: "deferred",
                                           True: "goahead",
                                           "item": "moved from another map"}:
        try:
            item = self[key]
        except KeyError:
            # the same key cannot be found within the same namespace
            dstIndex = self._baseIndexForMap(mapId) + len(self._maps[mapId])
            self._model.sigBeforeInsert.emit(dstIndex)
            return True  # tell the map to go ahead to insert

        if item.isDeletionPending:
            # move from another map within the same namespace
            record = self._pendingDeletions[key]
            srcMapId = record.fromMap
            srcIndex = self._baseIndexForMap(srcMapId) + self._maps[srcMapId].index(key)
            dstIndex = self._baseIndexForMap(mapId) + len(self._maps[mapId])

            if srcIndex == dstIndex or (srcIndex + 1 == dstIndex):
                # srcIndex == dstIndex -> Invalid move, prohibited by Qt
                # srcIndex == dstIndex -> No-op move, also causes problems with Qt
                needMoveRow = False
            else:
                needMoveRow = True

            if needMoveRow:
                # start to move
                self._model.sigBeforeMove.emit(srcIndex, dstIndex)

            del self._maps[srcMapId][key]
            item.isDeletionPending = False
            del self._pendingDeletions[key]
            self._maps[mapId][key] = item

            if needMoveRow:
                self._model.sigAfterMove.emit()
            return item
        else:
            # The item hasn't been marked pending deletion.
            # return False so that the map should skip this one.
            print("deferred", key)
            return False

    def afterInsert(self):
        self._model.sigAfterInsert.emit()

    def markPendingDeletion(self, mapId, key):
        item = self._maps[mapId][key]
        if item.isDeletionPending:
            return
        assert key not in self._pendingDeletions
        item.isDeletionPending = True
        self._pendingDeletions[key] = PendingDeletionRecord(
            fromMap = mapId,
            mapTicks = self._getTickCounts(mapId))

    def doneUpdating(self, mapId):
        namespace = self._reversedMapNamespaces[mapId]
        nsMaps = self._mapNamespaces[namespace]
        for key, record in self._pendingDeletions.copy().items():
            if record.fromMap not in nsMaps:
                # not the same namespace
                continue
            else:
                now = self._getTickCounts(mapId)
                ticks = record.mapTicks
                if not all(map(lambda pair: pair[0] < pair[1], zip(ticks, now))):
                    continue

                baseIndex = self._baseIndexForMap(record.fromMap)
                i = baseIndex + self._maps[record.fromMap].index(key)

                self._model.beginRemoveRows(QModelIndex(), i, i)
                del self._maps[record.fromMap][key]
                del self._pendingDeletions[key]
                self._model.endRemoveRows()

        self._mapTickCount[mapId] += 1

    def _getTickCounts(self, mapId):
        # return the tick count for the entire namespace like [0, 1, 1, 1]
        namespace = self._reversedMapNamespaces[mapId]
        mapIds = self._mapNamespaces[namespace]
        result = [self._mapTickCount[mapId_] for mapId_ in mapIds]
        return result
