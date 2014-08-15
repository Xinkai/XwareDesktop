# -*- coding: utf-8 -*-

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QIcon
from PyQt5.QtQuick import QQuickImageProvider


class IconProvider(QQuickImageProvider):
    def __init__(self):
        super().__init__(QQuickImageProvider.Pixmap)

    @pyqtSlot(str, "QSize")
    def requestPixmap(self, id_, size):
        name = id_

        if not size.isValid():
            raise ValueError("{} is not valid".format(size))

        return QIcon.fromTheme(name).pixmap(size), size
