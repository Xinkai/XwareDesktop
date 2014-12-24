# -*- coding: utf-8 -*-

from collections import OrderedDict
import threading


class TaskMapBase(OrderedDict):
    """TaskModel underlying data"""
    _Lock = threading.Lock()
    _Item = None  # "the class with which new task item can be created"

    def __init__(self, *,
                 klass: "this map is used for this kind of map, native to the adapter"):
        super().__init__()
        self.__klass = klass
        self.__adapter = None  # TODO: remove this?
        self.__namespace = None
        self.__klassMap = None
        self.__taskModel = None

    def update(self, *args, **kwargs):
        raise NotImplementedError("use updateTaskMap")

    def updateData(self, updating: dict):
        with self.__class__._Lock:
            currentKeys = set(self.keys())
            updatingKeys = set(updating.keys())

            addedKeys = updatingKeys - currentKeys
            modifiedKeys = updatingKeys & currentKeys  # Alter/change/modify
            removedKeys = currentKeys - updatingKeys

            for k in modifiedKeys:
                self[k].update(updating[k], self.__klass)

            for k in addedKeys:
                self.insert(k, updating[k])

            for k in removedKeys:
                del self.__klassMap[k]
            self.__klassMap.doneUpdating(self.__klass)

    def insert(self, key, value) -> None:
        ret = self.__klassMap.beforeInsert(self.__klass, key)
        if ret is True:
            assert self.namespace, "namespace must be set."
            assert self.__taskModel, "taskModel must be set."
            item = self.__class__._Item(
                namespace = self.namespace,
                taskModel = self.__taskModel,
            )
            from PyQt5.QtCore import QCoreApplication
            app = QCoreApplication.instance()
            if app:
                item.moveToThread(QCoreApplication.instance().thread())
                item.setParent(self.__taskModel)
            item.update(value, self.__klass)
            self[key] = item
            return self.__klassMap.afterInsert()

        elif isinstance(ret, self.__class__._Item):
            assert key in self
            item = ret
            return item.update(value, self.__klass)

        elif ret is False:
            return
        raise RuntimeError("Unknown return value of beforeInsert:", ret)

    def index(self, key):
        return list(self.keys()).index(key)

    @property
    def klass(self) -> int:
        return self.__klass

    @property
    def namespace(self) -> str:
        if not self.__namespace:
            raise RuntimeError("namespace must be set before being used.")
        return self.__namespace

    @namespace.setter
    def namespace(self, value):
        self.__namespace = value

    def setKlassMap(self, value):
        self.__klassMap = value

    def setAdapter(self, adapter: object):
        self.__adapter = adapter

    def setTaskModel(self, taskModel: object):
        self.__taskModel = taskModel
