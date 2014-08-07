# -*- coding: utf-8 -*-

import logging
import enum


@enum.unique
class ActWhen(enum.IntEnum):
    ALL_TASKS_COMPLETED = 0
    SELECTED_TASKS_COMPLETED = 1

    def __str__(self):
        if self == self.__class__.ALL_TASKS_COMPLETED:
            return "所有的任务完成时"
        elif self == self.__class__.SELECTED_TASKS_COMPLETED:
            return "选中的任务完成时"
        else:
            raise ValueError()


@enum.unique
class Action(enum.IntEnum):
    Null = 0
    PowerOff = 1
    HybridSleep = 2
    Hibernate = 3
    Suspend = 4

    def __str__(self):
        if self == self.__class__.Null:
            return "无"
        elif self == self.__class__.PowerOff:
            return "关机"
        elif self == self.__class__.HybridSleep:
            return "混合休眠"
        elif self == self.__class__.Hibernate:
            return "休眠"
        elif self == self.__class__.Suspend:
            return "睡眠"
        else:
            raise ValueError()
