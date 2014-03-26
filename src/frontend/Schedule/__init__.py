# -*- coding: utf-8 -*-

import logging

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

ALL_TASKS_COMPLETED = 0
SELECTED_TASKS_COMPLETED = 1

ACTION_NONE = 0
ACTION_SLEEP = 1
ACTION_HIBERNATE = 2
ACTION_SHUTDOWN = 3

# Scheduler controls what happens when tasks finished.
class Scheduler(QObject):
    sigSchedulerSummaryUpdated = pyqtSignal()

    POSSIBLE_ACTWHENS = (
        (ALL_TASKS_COMPLETED, "所有的"),
        (SELECTED_TASKS_COMPLETED, "选中的"),
    )

    POSSIBLE_ACTIONS = (
        (ACTION_NONE, "无"),
        (ACTION_SLEEP, "睡眠"),
        (ACTION_HIBERNATE, "休眠"),
        (ACTION_SHUTDOWN, "关机"),
    )

    app = None
    _action = ACTION_NONE
    _actWhen = ALL_TASKS_COMPLETED
    _waitingTaskIds = set()         # user-selected tasks
    _stillWaitingTasksNumber = 0    # user-selected tasks - nolonger running tasks
    def __init__(self, app):
        super().__init__(app)
        self.app = app

        self.app.etmpy.runningTasksStat.sigTaskNolongerRunning.connect(self.slotMayAct)
        self.app.etmpy.runningTasksStat.sigTaskAdded.connect(self.slotMayAct)

    @property
    def actWhen(self):
        # tasks
        return self._actWhen

    @actWhen.setter
    def actWhen(self, value):
        raise NotImplementedError("use set method")

    @property
    def waitingTaskIds(self):
        return self._waitingTaskIds

    @waitingTaskIds.setter
    def waitingTaskIds(self, value):
        raise NotImplementedError("use set method")

    @property
    def action(self):
        return self._action

    @action.setter
    def action(self, value):
        raise NotImplementedError("use set method")

    @classmethod
    def getActionName(cls, actionId):
        return cls.POSSIBLE_ACTIONS[actionId][1]

    def getSummary(self):
        # return either False / str
        # False -> scheduled to do something
        # str -> one sentence summary
        if self.action == ACTION_NONE:
            return False

        if self._stillWaitingTasksNumber:
            return "{}个任务结束后{}".format(self._stillWaitingTasksNumber,
                                            self.getActionName(self._action))

    @pyqtSlot(int)
    def slotMayAct(self):
        if self.action == ACTION_NONE:
            self.sigSchedulerSummaryUpdated.emit()
            logging.info("cancel schedule because action is none")
            return

        runningTaskIds = self.app.etmpy.runningTasksStat.getTIDs()
        if self.actWhen == SELECTED_TASKS_COMPLETED:
            stillWaitingTaskIds = set(runningTaskIds) & self.waitingTaskIds
            self._stillWaitingTasksNumber = len(stillWaitingTaskIds)
        elif self.actWhen == ALL_TASKS_COMPLETED:
            self._stillWaitingTasksNumber = len(runningTaskIds)
        else:
            raise Exception("Unknown actWhen.")

        if self._stillWaitingTasksNumber > 0:
            self.sigSchedulerSummaryUpdated.emit()
            logging.info("not take action because desired tasks are running.")
            return

        self.sigSchedulerSummaryUpdated.emit()

        if self.action == ACTION_HIBERNATE:
            print("HIBERNATE")
        elif self.action == ACTION_SLEEP:
            print("SLEEP")
        elif self.action == ACTION_SHUTDOWN:
            print("SHUTDOWN")
        else:
            raise Exception("Unknown action")

    def set(self, actWhen, taskIds, action):
        if actWhen == SELECTED_TASKS_COMPLETED:
            self._actWhen, self._waitingTaskIds, self._action = actWhen, taskIds, action
        else:
            self._actWhen, self._action = actWhen, action

        self.slotMayAct()
