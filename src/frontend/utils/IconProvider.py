# -*- coding: utf-8 -*-

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QIcon
from PyQt5.QtQuick import QQuickImageProvider

import os, mimetypes


if not mimetypes.inited:
    mimetypes.init()


class IconProvider(QQuickImageProvider):
    def __init__(self):
        super().__init__(QQuickImageProvider.Pixmap)

    @pyqtSlot(str, "QSize")
    def requestPixmap(self, id_, size):
        name = id_

        if not size.isValid():
            raise ValueError("{} is not valid".format(size))

        return QIcon.fromTheme(name).pixmap(size), size


class MimeIconProvider(QQuickImageProvider):
    def __init__(self):
        super().__init__(QQuickImageProvider.Pixmap)

    @pyqtSlot(str, "QSize")
    def requestPixmap(self, fullpath, size):
        if os.path.isdir(fullpath):
            return QIcon.fromTheme("folder").pixmap(size), size

        ext = os.path.splitext(fullpath)[1]
        try:
            mimetype = mimetypes.types_map[ext]
        except KeyError:
            mimetype = "file"

        mimetype = mimetype.replace("/", "-")
        return QIcon.fromTheme(mimetype, QIcon.fromTheme("file")).pixmap(size), size
