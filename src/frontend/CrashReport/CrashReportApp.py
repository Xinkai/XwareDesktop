#!/usr/bin/python3
# -*- coding: utf-8 -*-

from PyQt5.Qt import pyqtSlot, QDesktopServices, QUrl
from PyQt5.QtWidgets import QDialog, QApplication
from ui_crashreport import Ui_Dialog
import os, sys, subprocess
import html
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../"))
try:
    from shared import __githash__
except ImportError:
    __githash__ = None
from __init__ import CrashReport


class CrashReportForm(QDialog, Ui_Dialog):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setupUi(self)

        self.pushButton_github.clicked.connect(self.reportToGithub)
        self.pushButton_close.clicked.connect(self.reportToNone)

    def setPayload(self, payload):
        if not __githash__:
            githash = "开发版"
        else:
            githash = __githash__

        self.textBrowser.setHtml(
            "发行版: {lsb_release}<br />"
            "桌面环境: {xdg_current_desktop}/{desktop_session}<br />"
            "版本: {githash}<br /><br />"
            "<b style='color: orange'>补充描述计算机。</b><br />可留空。<br /><br />"

            "<b style='color: orange'>简述在什么情况下发生了这个问题。</b><br />可留空。<br /><br />"

            "======================== 报告 ========================<br />"
            "错误发生在{threadName}<br />"
            "```<pre style='color:grey; font-family: Arial;'>"
            "{traceback}"
            "</pre>```<br />"
            "======================== 结束 ========================<br />"
            .format(lsb_release = self.lsb_release(),
                    xdg_current_desktop = os.environ.get("XDG_CURRENT_DESKTOP", "未知"),
                    desktop_session = os.environ.get("DESKTOP_SESSION", "未知"),
                    githash = githash,
                    threadName = payload["thread"],
                    traceback = html.escape(payload["traceback"]))
        )

    @staticmethod
    def lsb_release():
        try:
            with subprocess.Popen(["lsb_release", "-idrcs"], stdout = subprocess.PIPE) as proc:
                return proc.stdout.read().decode("UTF-8")
        except FileNotFoundError:
            return "发行版类型及版本获取失败。"

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
        if len(argv) > 1:
            payload = CrashReport.decodePayload(argv[1])
        else:
            payload = {
                "thread": "测试线程",
                "traceback": """Traceback (most recent call last):
  File "<模拟崩溃报告>", line 1, in <module>
ZeroDivisionError: division by zero""",
            }
        self.form.setPayload(payload)
        self.form.show()

if __name__ == "__main__":
    app = CrashReportApp(sys.argv)
    sys.exit(app.exec())
