# -*- coding: utf-8 -*-

import logging
from launcher import app


class AllowDrop(object):
    def setupDropSupport(self):
        self.setAcceptDrops(True)

    def dropEvent(self, qDropEvent):
        if qDropEvent.source() is not None:
            return  # drag starts within the application
        mimeData = qDropEvent.mimeData()

        if mimeData.hasUrls():
            logging.info("drop action: hasUrls.")
            urls = list(map(lambda qurl: qurl.url(), mimeData.urls()))
            app.frontendpy.taskCreationAgent.createTasksAction(urls)
        elif mimeData.hasText():
            logging.info("drop action: hasText.")
            app.frontendpy.taskCreationAgent.createTasksFromMimeData(mimeData)
        else:
            pass
        qDropEvent.acceptProposedAction()

    def dragMoveEvent(self, dragMoveEvent):
        # even this is a noop, it's required for dropEvent to be called.
        pass

    def dragEnterEvent(self, dragEnterEvent):
        dragEnterEvent.acceptProposedAction()
