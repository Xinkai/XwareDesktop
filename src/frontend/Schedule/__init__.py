# -*- coding: utf-8 -*-

import logging

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from Schedule.SchedulerCountdown import CountdownMessageBox
from Schedule.PowerAction import PowerActionManager, ACTION_NONE

ALL_TASKS_COMPLETED = 0
SELECTED_TASKS_COMPLETED = 1


class Scheduler(QObject):
    # connects PowerActionManager and SchedulerWin, also does confirmation.

    sigSchedulerSummaryUpdated = pyqtSignal()
    sigActionConfirmed = pyqtSignal(bool)

    POSSIBLE_ACTWHENS = (
        (ALL_TASKS_COMPLETED, "所有的"),
        (SELECTED_TASKS_COMPLETED, "选中的"),
    )

    app = None
    _actionId = None
    _actWhen = None
    _waitingTaskIds = None         # user-selected tasks
    _stillWaitingTasksNumber = 0   # (computed) user-selected tasks - nolonger running tasks
    confirmDlg = None

    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self._waitingTaskIds = set()
        self.reset()

        self.powerActionManager = PowerActionManager(self)
        self.actions = self.powerActionManager.actions

        self.app.etmpy.runningTasksStat.sigTaskNolongerRunning.connect(self.slotMayAct)
        self.app.etmpy.runningTasksStat.sigTaskAdded.connect(self.slotMayAct)
        self.sigActionConfirmed[bool].connect(self.slotConfirmed)

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
    def actionId(self):
        return self._actionId

    @actionId.setter
    def actionId(self, value):
        raise NotImplementedError("use set method")

    def getActionNameById(self, actionId):
        return self.powerActionManager.getActionById(actionId).displayName

    def getSummary(self):
        # return either True / False / str
        # True -> action undergoing, system shutting down
        # False -> scheduled to do nothing
        # str -> one sentence summary
        if self.actionId == ACTION_NONE:
            return False

        if self._stillWaitingTasksNumber:
            return "{}个任务结束后{}".format(
                self._stillWaitingTasksNumber,
                self.getActionNameById(self.actionId))
        else:
            return True

    @pyqtSlot(int)
    def slotMayAct(self):
        if self.actionId == ACTION_NONE:
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

        self.confirmDlg = CountdownMessageBox(self.getActionNameById(self.actionId))
        self.confirmDlg.show()
        self.confirmDlg.activateWindow()
        self.confirmDlg.raise_()

    def set(self, actWhen, taskIds, actionId):
        if actWhen == SELECTED_TASKS_COMPLETED:
            self._actWhen, self._waitingTaskIds, self._actionId = actWhen, taskIds, actionId
        else:
            self._actWhen, self._actionId = actWhen, actionId

        self.slotMayAct()

    def reset(self):
        # Should be called when
        # 1. app starts up
        # 2. immediately before power-control commands are run
        # 3. action is canceled by user
        self.set(ALL_TASKS_COMPLETED, set(), ACTION_NONE)

    @pyqtSlot(int)
    def slotConfirmed(self, confirmed):
        del self.confirmDlg
        if confirmed:
            _actionId = self.actionId
            self.powerActionManager.act(_actionId)
            self.reset()
        else:
            self.reset()
