#!/usr/bin/python3
# -*- coding: utf-8 -*-

from PyQt5.Qt import pyqtSlot, QDesktopServices, QUrl
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QDialog, QApplication
from ui_crashreport import Ui_Dialog
import os, sys
import html
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../"))
try:
    from shared import __githash__
except ImportError:
    __githash__ = None

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../"))
from utils.system import getDistro

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
            "{platform}"
            "应用程序版本: {githash}<br /><br />"
            "<b style='color: orange'>补充描述计算机。</b><br />可留空。<br /><br />"
            "<b style='color: orange'>简述在什么情况下发生了这个问题。</b><br />可留空。<br /><br />"
            "======================== 报告 ========================<br />"
            "错误发生在{threadName}<br />"
            "```<pre style='color:grey; font-family: Arial;'>"
            "{traceback}"
            "</pre>```<br />"
            "======================== 结束 ========================<br />"
            .format(platform = self.getPlatform(),
                    githash = githash,
                    threadName = payload["thread"],
                    traceback = html.escape(payload["traceback"]))
        )

    @staticmethod
    def getPlatform():
        if sys.platform == "linux":
            return \
                "发行版: {distro.name} {distro.version}<br />" \
                "桌面环境: {xdg_current_desktop}/{desktop_session}<br />" \
                .format(distro = getDistro(),
                        xdg_current_desktop = os.environ.get("XDG_CURRENT_DESKTOP", "未知"),
                        desktop_session = os.environ.get("DESKTOP_SESSION", "未知"))
        elif sys.platform == "win32":
            import platform
            return \
                "操作系统：Windows {uname.release} {uname.version}<br />" \
                .format(uname = platform.uname())

        else:
            return "获取系统相关信息失败。<br />"

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
        font = QFont()
        font.setPointSize(10)
        self.setFont(font)

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
        self.aboutToQuit.connect(self.cleanUp)

    @pyqtSlot()
    def cleanUp(self):
        del self.form

if __name__ == "__main__":
    app = CrashReportApp(sys.argv)

    def safeExec(app_):
        code = app_.exec()
        windows = app_.topLevelWindows()
        if windows:
            raise RuntimeError("Windows left: {}"
                               .format(list(map(lambda win: win.objectName(),
                                                windows))))
        del app_
        sys.exit(code)
    safeExec(app)
