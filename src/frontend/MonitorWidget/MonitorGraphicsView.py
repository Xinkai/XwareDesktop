# -*- coding: utf-8 -*-

import logging

from PyQt5.QtCore import QPointF, pyqtSlot, Qt
from PyQt5.QtGui import QPolygonF, QPen, QBrush, QLinearGradient
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene

from DragDrop import AllowDrop


class MonitorGraphicsView(QGraphicsView, AllowDrop):
    monitorWin = None

    SIZE = (50.0, 50.0)
    FULLSPEED = 512 * 1024  # 512 in kb/s

    _progressText = None
    _speedsPolygon = None
    _speedsPen = None
    _speedsBrush = None

    def __init__(self, parent = None):
        super().__init__(parent)
        self.monitorWin = parent
        if self.monitorWin:
            self.monitorWin.sigTaskUpdating.connect(self.slotTaskUpdate)

        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(0, 0, self.SIZE[0], self.SIZE[1])
        self.setScene(self.scene)

        self._speedsPen = QPen(Qt.white)

        gradient = QLinearGradient(0, 0, self.SIZE[0], self.SIZE[1])
        gradient.setColorAt(0.0, Qt.darkGreen)
        gradient.setColorAt(1.0, Qt.yellow)
        self._speedsBrush = QBrush(gradient)

        # add elements to the scene
        self._speedsPolygon = self.scene.addPolygon(QPolygonF(),
                                                    self._speedsPen,
                                                    self._speedsBrush)
        self._progressText = self.scene.addText("")
        self._progressText.setPos(10, 0)

        self.setupDropSupport()

    def mousePressEvent(self, qMouseEvent):
        self.monitorWin.mousePressEvent(qMouseEvent)

    def mouseMoveEvent(self, qMouseEvent):
        self.monitorWin.mouseMoveEvent(qMouseEvent)

    def mouseReleaseEvent(self, qMouseEvent):
        self.monitorWin.mouseReleaseEvent(qMouseEvent)

    def _setSpeeds(self, speeds):
        polygon = QPolygonF()
        polygon.append(QPointF(0, self.SIZE[1]))  # start the polygon

        nSamples = len(speeds)
        xPerSample = self.SIZE[0] / nSamples

        for i, speed in enumerate(speeds):
            y = self._translateSpeedToPosY(speed)
            polygon.append(QPointF(xPerSample * i, y))
            polygon.append(QPointF(xPerSample * (i + 1), y))
        polygon.append(QPointF(*self.SIZE))  # close the polygon

        self._speedsPolygon.setPolygon(polygon)

    def _setProgress(self, process):  # 10000 means 100%
        if process is None:
            self._progressText.setPlainText("")
        else:
            self._progressText.setPlainText("{:.1f}%".format(process / 100))

    def _translateSpeedToPosY(self, speed):
        return self.SIZE[1] * (1.0 - speed / self.FULLSPEED)

    @pyqtSlot(dict)
    def slotTaskUpdate(self, task):
        if task:
            self._setProgress(task["progress"])
            self._setSpeeds(task["speeds"])
        else:
            self._setProgress(None)
            self._setSpeeds([0.0])