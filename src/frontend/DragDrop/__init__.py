# -*- coding: utf-8 -*-

import logging

from PyQt5.QtGui import QGuiApplication

class AllowDrop(object):
    def setupDropSupport(self):
        self._actionsQueue = QGuiApplication.instance().mainWin.frontendpy.queue
        self.setAcceptDrops(True)

    def dropEvent(self, qDropEvent):
        print("event drop")
        if qDropEvent.source() is not None:
            return # drag starts within the application
        mimeData = qDropEvent.mimeData()

        if mimeData.hasUrls():
            logging.info("drop action: hasUrls.")
            urls = list(map(lambda qurl: qurl.url(), mimeData.urls()))
            self._actionsQueue.createTasksAction(urls)
        elif mimeData.hasText():
            logging.info("drop action: hasText.")
            self._actionsQueue.createTasksFromMimeData(mimeData)
        else:
            pass
        qDropEvent.acceptProposedAction()

    def dragEnterEvent(self, dragEnterEvent):
        print("dragenter", dragEnterEvent.proposedAction())
        dragEnterEvent.acceptProposedAction()
