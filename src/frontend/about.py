# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog

from shared import __version__, XWARE_VERSION
try:
    from shared import __githash__
except ImportError:
    __githash__ = None
from ui_about import Ui_dlg_about


class AboutDialog(QDialog, Ui_dlg_about):
    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.fillLibVersions()

    def fillLibVersions(self):
        if __githash__:
            self.label_githash.setText(__githash__)

        self.label_version.setText(__version__)

        self.label_xwareVer.setText(XWARE_VERSION)

        from PyQt5.Qt import QT_VERSION, QT_VERSION_STR, PYQT_VERSION, PYQT_VERSION_STR
        self.label_qtVer.setText("{} ({})".format(QT_VERSION_STR, QT_VERSION))
        self.label_pyqtVer.setText("{} ({})".format(PYQT_VERSION_STR, PYQT_VERSION))

        import sys
        self.label_pythonVer.setText(".".join(map(str, sys.version_info)))

        import requests
        self.label_requestsVer.setText(requests.__version__)

        import pyinotify
        self.label_pyinotifyVer.setText(pyinotify.__version__)

        from PyQt5 import QtWebKit
        self.label_qtwebkitVer.setText(QtWebKit.qWebKitVersion())
