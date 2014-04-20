#!/usr/bin/python3
# -*- coding: utf-8 -*-

from PyQt5.Qt import pyqtSlot, QDesktopServices, QUrl
from PyQt5.QtWidgets import QDialog, QApplication
from ui_crashreport import Ui_Dialog
import sys
from __init__ import CrashReport


class CrashReportForm(QDialog, Ui_Dialog):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setupUi(self)

        self.pushButton_github.clicked.connect(self.reportToGithub)
        self.pushButton_close.clicked.connect(self.reportToNone)

    def setPayload(self, payload):
        self.textBrowser.setText(
            "错误发生在{threadName}\n\n"
            "{traceback}\n"
            "============================ 结束 ============================\n"
            .format(threadName = payload["thread"],
                    traceback = payload["traceback"])
        )

    @pyqtSlot()
    def reportToGithub(self):
        qurl = QUrl("http://github.com/Xinkai/XwareDesktop/issues/new")
        QDesktopServices.openUrl(qurl)

    @pyqtSlot()
    def reportToNone(self):
        self.close()


class CrashReportApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.form = CrashReportForm()
        payload = CrashReport.decodePayload(argv[1])
        self.form.setPayload(payload)
        self.form.show()

if __name__ == "__main__":
    app = CrashReportApp(sys.argv)
    sys.exit(app.exec())
