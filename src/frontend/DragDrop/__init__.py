# -*- coding: utf-8 -*-

import logging
from launcher import app
from PyQt5.QtCore import QByteArray
from PyQt5.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent


class AllowDrop(object):
    def setupDropSupport(self):
        self.setAcceptDrops(True)

    def dropEvent(self, event: QDropEvent):
        if event.source() is not None:
            return  # drag starts within the application
        mimeData = event.mimeData()

        if mimeData.hasUrls():
            raw = mimeData.data("text/uri-list")
            if type(raw) == QByteArray:
                # Compat. Workaround #113
                # As of Qt 5.3.1, QMimeData.urls() cannot read UTF-16 encoded QByteArray
                # the format Chrome passes over.
                # Use special tactic!
                url = bytes(raw).decode("UTF-16LE")
                urls = [url]
            else:
                urls = list(map(lambda qurl: qurl.url(), mimeData.urls()))
            app.taskCreationAgent.createTasksAction(urls)
        elif mimeData.hasText():
            app.taskCreationAgent.createTasksFromMimeData(mimeData)
        else:
            pass
        event.acceptProposedAction()

    def dragMoveEvent(self, event: QDragMoveEvent):
        # even this is a noop, it's required for dropEvent to be called.
        pass

    def dragEnterEvent(self, event: QDragEnterEvent):
        event.acceptProposedAction()
