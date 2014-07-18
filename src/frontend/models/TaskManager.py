# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-

import asyncio
import collections
from functools import partial
from itertools import islice

from PyQt5.QtCore import QModelIndex


class TaskManager(collections.MutableMapping):
    _mapNamespaces = collections.defaultdict(list)  # {"xware-0123": [0, 1, 2, 3], ...}

    def __init__(self, model):
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
        raise NotImplementedError()

    def __getitem__(self, key):
        # faster than ChainMap's implementation
        ns = key.split("|")[0]
        for nsmap in self._mapsForNamespace(ns):
            try:
                result = nsmap[key]
                result["ns"] = ns
                return result
            except KeyError:
                pass
        raise KeyError("key {} cannot be found.".format(key))

    def __iter__(self):
        for map_ in self._maps:
            yield from map_

    def __len__(self):
        return sum(map(len, self._maps))

    def __contains__(self, key):
        # faster than ChainMap's implementation
        ns = key.split("|")[0]
        return any(key in nsmap for nsmap in self._mapsForNamespace(ns))

    # Custom implementation
    def _mapsForNamespace(self, ns):
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
                result["ns"] = self._maps[mapId].namespace
                return result
        raise IndexError("Out of range: index({})".format(index))

    @asyncio.coroutine
    def appendMap(self, map_):
        # All tasks from all backends live in a same chainmap, therefore id needs to be prefixed

        if not isinstance(map_, collections.OrderedDict):
            raise ValueError("Can only register OrderedDict")

        namespace = getattr(map_, "namespace")
        if not namespace:
            raise ValueError("Map must have a namespace property")

        assert not bool(map_), "Map must be empty before registering"

        mapId = len(self._maps)
        self._maps.append(map_)

        # implement map's model related methods
        map_.beforeInsert = partial(self.beforeInsert, mapId)
        map_.afterInsert = self.afterInsert
        map_.beforeModify = partial(self.beforeModify, mapId)
        map_.afterModify = partial(self.afterModify, mapId)
        map_.beforeDelete = partial(self.beforeDelete, mapId)
        map_.afterDelete = self.afterDelete

        self._mapNamespaces[namespace].append(mapId)
        return mapId

    def updateMap(self, mapId, updating):
        self._maps[mapId].updateData(updating)

    def beforeInsert(self, mapId, key):
        if key in self:
            print("deferred", key)
            return False  # deferred
        baseIndex = self._baseIndexForMap(mapId)
        size = len(self._maps[mapId])
        i = baseIndex + size

        self._model.sigBeforeInsert.emit(i)
        return True

    def afterInsert(self):
        self._model.sigAfterInsert.emit()

    def beforeModify(self, mapId):
        pass

    def afterModify(self, mapId, index0, index1):
        baseIndex = self._baseIndexForMap(mapId)
        i0 = baseIndex + index0
        i1 = baseIndex + index1 - 1
        self._model.sigAfterModify.emit(i0, i1)

    def beforeDelete(self, mapId, index):
        baseIndex = self._baseIndexForMap(mapId)
        i = baseIndex + index

        self._model.beginRemoveRows(QModelIndex(), i, i)
        return True

    def afterDelete(self):
        self._model.endRemoveRows()
