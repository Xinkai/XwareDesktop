# -*- coding: utf-8 -*-

import logging
from launcher import app

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QStatusBar

from .CStatusBarLabel import CustomStatusBarLabel
from legacy.SchedulerButton import SchedulerButton
from Settings.QuickSpeedLimit import QuickSpeedLimitBtn
from utils.misc import debounce, getHumanBytesNumber


class CustomStatusBar(QStatusBar):
    xwaredStatus = None
    etmStatus = None
    frontendStatus = None
    quickSpeedLimitBtn = None
    schedulerBtn = None
    spacer = None
    dlStatus = None
    ulStatus = None

    def __init__(self, parent = None):
        super().__init__(parent)
        self.setupStatusBar()

    def setupStatusBar(self):
        self.xwaredStatus = CustomStatusBarLabel(self)
        self.etmStatus = CustomStatusBarLabel(self)
        self.frontendStatus = CustomStatusBarLabel(self)

        self.quickSpeedLimitBtn = QuickSpeedLimitBtn(self)
        self.schedulerBtn = SchedulerButton(self)

        self.spacer = CustomStatusBarLabel(self)
        sp = self.spacer.sizePolicy()
        sp.setHorizontalStretch(1)
        self.spacer.setSizePolicy(sp)

        self.dlStatus = CustomStatusBarLabel(self)
        self.ulStatus = CustomStatusBarLabel(self)

        app.adapterManager[0].infoUpdated.connect(self.slotXwaredStatusUpdated)
        app.frontendpy.sigFrontendStatusChanged.connect(self.slotFrontendStatusChanged)
        app.etmpy.sigTasksSummaryUpdated[bool].connect(self.slotTasksSummaryUpdated)
        app.etmpy.sigTasksSummaryUpdated[dict].connect(self.slotTasksSummaryUpdated)

    @pyqtSlot()
    def slotXwaredStatusUpdated(self):
        xwaredStatus = app.adapterManager[0].xwaredRunning

        app.mainWin.menu_backend.setEnabled(xwaredStatus)
        if xwaredStatus:
            self.xwaredStatus.setText(
                "<img src=':/image/check.png' width=14 height=14>"
                "<font color='green'>xwared</font>")
            self.xwaredStatus.setToolTip("<div style='color:green'>xwared运行中</div>")
        else:
            self.xwaredStatus.setText(
                "<img src=':/image/attention.png' width=14 height=14>"
                "<font color='red'>xwared</font>")
            self.xwaredStatus.setToolTip("<div style='color:red'>xwared未启动</div>")

        etmStatus = app.adapterManager[0].etmPid != 0

        app.mainWin.action_ETMstart.setEnabled(not etmStatus)
        app.mainWin.action_ETMstop.setEnabled(etmStatus)
        app.mainWin.action_ETMrestart.setEnabled(etmStatus)

        overallCheck = False
        tooltips = []
        if etmStatus:
            activationStatus = app.etmpy.getActivationStatus()
            tooltips.append("<div style='color:green'>ETM运行中</div>")
            if activationStatus.status == 1:
                overallCheck = True
                tooltips.append(
                    "<div style='color:green'>"
                    "<img src=':/image/connected.png' width=16 height=16>"
                    "设备已激活</div>")
            else:
                tooltips.append(
                    "<div style='color:red'>"
                    "<img src=':/image/disconnected.png' width=16 height=16>"
                    "设备未激活</div>")
        else:
            tooltips.append("<div style='color:red'>ETM未启动</div>")

        if overallCheck:
            self.etmStatus.setText(
                "<img src=':/image/check.png' width=14 height=14>"
                "<font color='green'>ETM</font>")
        else:
            self.etmStatus.setText(
                "<img src=':/image/attention.png' width=14 height=14>"
                "<font color='red'>ETM</font>")

        self.etmStatus.setToolTip("".join(tooltips))

    @pyqtSlot()
    @debounce(0.5, instant_first = True)
    def slotFrontendStatusChanged(self):
        frontendStatus = app.frontendpy.getFrontendStatus()
        if all(frontendStatus):
            self.frontendStatus.setText(
                "<img src=':/image/check.png' width=14 height=14><font color='green'>Web前端</font>")
        else:
            self.frontendStatus.setText(
                "<img src=':/image/attention.png' width=14 height=14>"
                "<font color='red'>Web前端</font>")

        tooltipTemplate = \
            "<div style='color:{}'>页面代码已插入</div>\n" \
            "<div style='color:{}'>设备已登录</div>\n" \
            "<div style='color:{}'>设备在线</div>"
        tooltip = tooltipTemplate.format(*map(lambda s: "green" if s else "red", frontendStatus))

        self.frontendStatus.setToolTip(tooltip)
        logging.info(frontendStatus)

    @pyqtSlot(bool)
    @pyqtSlot(dict)
    def slotTasksSummaryUpdated(self, summary):
        if not summary:
            self.dlStatus.setText(
                "<img src=':/image/down.png' height=14 width=14>获取下载状态失败"
            )
            self.dlStatus.setToolTip("")
            self.ulStatus.setText(
                "<img src=':/image/up.png' height=14 width=14>获取上传状态失败"
            )
            return

        self.dlStatus.setText(
            "<img src=':/image/down.png' height=14 width=14>{}/s".format(
                getHumanBytesNumber(summary["dlSpeed"])))
        self.dlStatus.setToolTip("{}任务下载中".format(summary["dlNum"]))

        self.ulStatus.setText(
            "<img src=':/image/up.png' height=14 width=14>{}/s".format(
                getHumanBytesNumber(summary["upSpeed"]))
        )
