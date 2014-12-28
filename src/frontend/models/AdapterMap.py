# -*- coding: utf-8 -*-

from collections import OrderedDict
from collections.abc import Sized, Iterable, Container
from itertools import islice

from .KlassMap import KlassMap


class AdapterMap(Sized, Iterable, Container):
    def __init__(self, model):
        self._klassMaps = OrderedDict()
        self.__model = model

    def items(self):
        for namespace, klassMap in self._klassMaps.items():
            for rid, item in klassMap.items():
                yield ("|".join([namespace, rid]), item)

    def __getitem__(self, nsid: str):
        ns, rid = nsid.split("|")
        return self._klassMaps[ns][rid]

    def __iter__(self):
        # gives an iterator of nsids
        for namespace, klassMap in self._klassMaps.items():
            for rid in klassMap:
                yield "|".join([namespace, rid])

    def __len__(self):
        return sum(map(len, self._klassMaps.values()))

    def __contains__(self, nsid: str):
        ns, rid = nsid.split("|")
        return (ns in self._klassMaps) and (rid in self._klassMaps[ns])

    # Custom implementation
    def baseIndexForAdapter(self, namespace: str):
        result = 0
        for a in self._klassMaps:
            if a == namespace:
                return result
            result += len(self._klassMaps[a])

    def at(self, index: "uint"):
        assert index >= 0, "index = {}".format(index)
        for namespace in self._klassMaps.keys():
            mapLIndex = self.baseIndexForAdapter(namespace)
            mapRIndex = mapLIndex + len(self._klassMaps[namespace]) - 1
            if mapRIndex >= index:
                inmapIndex = index - mapLIndex
                itr = islice(self._klassMaps[namespace].values(), inmapIndex, inmapIndex + 1)
                result = next(itr)
                return result
        raise IndexError("Out of range: index({})".format(index))

    def addKlassMap(self, klassMap: KlassMap):
        ns = klassMap.namespace
        if not ns:
            raise ValueError("Map must have a namespace property")

        if bool(klassMap):
            raise ValueError("KlassMap must be empty before registering")

        klassMap.setAdapterMap(self)
        self._klassMaps[ns] = klassMap

    def beforeRemove(self, namespace: str, klassIndex: int):
        baseIndex = self.baseIndexForAdapter(namespace)
        self.__model.sigBeforeRemove.emit(baseIndex + klassIndex)

    def afterRemove(self):
        self.__model.sigAfterRemove.emit()

    def beforeInsert(self, namespace: str, relDstIndex: int):
        baseIndex = self.baseIndexForAdapter(namespace)
        self.__model.sigBeforeInsert.emit(baseIndex + relDstIndex)

    def afterInsert(self):
        self.__model.sigAfterInsert.emit()

    def beforeMove(self, namespace: str, relSrcIndex: int, relDstIndex: int):
        baseIndex = self.baseIndexForAdapter(namespace)
        self.__model.sigBeforeMove.emit(baseIndex + relSrcIndex, baseIndex + relDstIndex)

    def afterMove(self):
        self.__model.sigAfterMove.emit()
