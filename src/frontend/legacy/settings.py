# -*- coding: utf-8 -*-

from launcher import app

from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtWidgets import QDialog, QTableWidgetItem, QButtonGroup, QFileDialog
from PyQt5.QtGui import QBrush

import os
from utils.system import getInitType, InitType

from .ui_settings import Ui_Dialog


class SettingsDialog(QDialog, Ui_Dialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.setupUi(self)

        self.lineEdit_loginUsername.setText(app.settings.get("account", "username"))
        self.lineEdit_loginPassword.setText(app.settings.get("account", "password"))
        self.checkBox_autoLogin.setChecked(app.settings.getbool("account", "autologin"))
        self.checkBox_autoStartFrontend.setChecked(app.autoStart)

        # Xwared Management
        managedBySystemd = app.adapterManager[0].daemonManagedBySystemd
        managedByUpstart = app.adapterManager[0].daemonManagedByUpstart
        managedByAutostart = app.adapterManager[0].daemonManagedByAutostart

        self.radio_managedBySystemd.setChecked(managedBySystemd)
        self.radio_managedByUpstart.setChecked(managedByUpstart)
        self.radio_managedByAutostart.setChecked(managedByAutostart)
        self.radio_managedByNothing.setChecked(
            not (managedBySystemd or managedByUpstart or managedByAutostart))

        initType = getInitType()
        self.radio_managedBySystemd.setEnabled(initType == InitType.SYSTEMD)
        self.radio_managedByUpstart.setEnabled(initType == InitType.UPSTART)

        # frontend
        self.checkBox_enableDevelopersTools.setChecked(
            app.settings.getbool("frontend", "enabledeveloperstools"))
        self.checkBox_allowFlash.setChecked(app.settings.getbool("frontend", "allowflash"))
        self.checkBox_minimizeToSystray.setChecked(
            app.settings.getbool("frontend", "minimizetosystray"))
        self.checkBox_closeToMinimize.setChecked(
            app.settings.getbool("frontend", "closetominimize"))
        self.checkBox_popNotifications.setChecked(
            app.settings.getbool("frontend", "popnotifications"))
        self.checkBox_notifyBySound.setChecked(
            app.settings.getbool("frontend", "notifybysound"))
        self.checkBox_showMonitorWindow.setChecked(
            app.settings.getbool("frontend", "showmonitorwindow"))
        self.spinBox_monitorFullSpeed.setValue(
            app.settings.getint("frontend", "monitorfullspeed"))

        # clipboard related
        self.checkBox_watchClipboard.stateChanged.connect(self.slotWatchClipboardToggled)
        self.checkBox_watchClipboard.setChecked(app.settings.getbool("frontend", "watchclipboard"))
        self.slotWatchClipboardToggled(self.checkBox_watchClipboard.checkState())
        self.plaintext_watchPattern.setPlainText(app.settings.get("frontend", "watchpattern"))

        self.btngrp_etmStartWhen = QButtonGroup()
        self.btngrp_etmStartWhen.addButton(self.radio_backendStartWhen1, 1)
        self.btngrp_etmStartWhen.addButton(self.radio_backendStartWhen2, 2)
        self.btngrp_etmStartWhen.addButton(self.radio_backendStartWhen3, 3)

        startEtmWhen = app.adapterManager[0].startEtmWhen
        if startEtmWhen:
            self.btngrp_etmStartWhen.button(startEtmWhen).setChecked(True)
        else:
            self.group_etmStartWhen.setEnabled(False)

        self.btn_addMount.clicked.connect(self.slotAddMount)
        self.btn_removeMount.clicked.connect(self.slotRemoveMount)

        # Mounts
        self.setupMounts()

        # backend setting is a different thing!
        self.setupETM()

    @pyqtSlot(int)
    def slotWatchClipboardToggled(self, state):
        self.plaintext_watchPattern.setEnabled(state)

    @pyqtSlot()
    def setupMounts(self):
        self.table_mounts.setRowCount(0)
        self.table_mounts.clearContents()

        mountsMapping = app.adapterManager[0].mountsFaker.getMountsMapping()
        for i, mount in enumerate(app.adapterManager[0].mountsFaker.mounts):
            self.table_mounts.insertRow(i)
            # drive1: the drive letter it should map to, by alphabetical order
            drive1 = app.adapterManager[0].mountsFaker.driveIndexToLetter(i)
            self.table_mounts.setItem(i, 0, QTableWidgetItem(drive1 + "\\TDDOWNLOAD"))

            # mounts = ['/path/to/1', 'path/to/2', ...]
            self.table_mounts.setItem(i, 1, QTableWidgetItem(mount))

            # drive2: the drive letter it actually is assigned to
            drive2 = mountsMapping.get(mount, "无")

            errors = []

            # check: mapping
            if drive1 != drive2:
                errors.append(
                    "错误：盘符映射在'{actual}'，而不是'{should}'。\n"
                    "如果这是个新挂载的文件夹，请尝试稍等，或重启后端，可能会修复此问题。"
                    .format(actual = drive2, should = drive1))

            brush = QBrush()
            if errors:
                brush.setColor(Qt.red)
                errString = "\n".join(errors)
            else:
                brush.setColor(Qt.darkGreen)
                errString = "正常"
            errWidget = QTableWidgetItem(errString)
            errWidget.setForeground(brush)

            self.table_mounts.setItem(i, 2, errWidget)
            del brush, errWidget

        self.table_mounts.resizeColumnsToContents()

    @pyqtSlot()
    def slotAddMount(self):
        fileDialog = QFileDialog(self, Qt.Dialog)
        fileDialog.setFileMode(QFileDialog.Directory)
        fileDialog.setOption(QFileDialog.ShowDirsOnly, True)
        fileDialog.setViewMode(QFileDialog.List)
        fileDialog.setDirectory(os.environ["HOME"])
        if fileDialog.exec():
            selected = fileDialog.selectedFiles()[0]
            if selected in self.newMounts:
                return
            row = self.table_mounts.rowCount()
            self.table_mounts.insertRow(row)
            self.table_mounts.setItem(
                row, 0,
                QTableWidgetItem(app.adapterManager[0].mountsFaker.driveIndexToLetter(row) +
                                 "\\TDDOWNLOAD"))
            self.table_mounts.setItem(row, 1, QTableWidgetItem(selected))
            self.table_mounts.setItem(row, 2, QTableWidgetItem("新近添加"))

    @pyqtSlot()
    def slotRemoveMount(self):
        row = self.table_mounts.currentRow()
        self.table_mounts.removeRow(row)

    @pyqtSlot()
    def accept(self):
        app.settings.set("account", "username", self.lineEdit_loginUsername.text())
        app.settings.set("account", "password", self.lineEdit_loginPassword.text())
        app.settings.setbool("account", "autologin", self.checkBox_autoLogin.isChecked())

        app.autoStart = self.checkBox_autoStartFrontend.isChecked()

        app.adapterManager[0].daemonManagedBySystemd = self.radio_managedBySystemd.isChecked()
        app.adapterManager[0].daemonManagedByUpstart = self.radio_managedByUpstart.isChecked()
        app.adapterManager[0].daemonManagedByAutostart = self.radio_managedByAutostart.isChecked()

        app.settings.setbool("frontend", "enabledeveloperstools",
                             self.checkBox_enableDevelopersTools.isChecked())
        app.settings.setbool("frontend", "allowflash",
                             self.checkBox_allowFlash.isChecked())
        app.settings.setbool("frontend", "minimizetosystray",
                             self.checkBox_minimizeToSystray.isChecked())

        # A possible Qt bug
        # https://bugreports.qt-project.org/browse/QTBUG-37695
        app.settings.setbool("frontend", "closetominimize",
                             self.checkBox_closeToMinimize.isChecked())
        app.settings.setbool("frontend", "popnotifications",
                             self.checkBox_popNotifications.isChecked())
        app.settings.setbool("frontend", "notifybysound",
                             self.checkBox_notifyBySound.isChecked())

        app.settings.setbool("frontend", "showmonitorwindow",
                             self.checkBox_showMonitorWindow.isChecked())
        app.settings.setint("frontend", "monitorfullspeed",
                            self.spinBox_monitorFullSpeed.value())
        app.settings.setbool("frontend", "watchclipboard",
                             self.checkBox_watchClipboard.isChecked())
        app.settings.set("frontend", "watchpattern",
                         self.plaintext_watchPattern.toPlainText())

        if self.group_etmStartWhen.isEnabled():
            startEtmWhen = self.btngrp_etmStartWhen.id(self.btngrp_etmStartWhen.checkedButton())
            app.adapterManager[0].startEtmWhen = startEtmWhen

        app.settings.save()

        app.adapterManager[0].mountsFaker.mounts = self.newMounts
        app.settings.applySettings.emit()
        super().accept()

    @property
    def newMounts(self):
        return list(map(lambda row: self.table_mounts.item(row, 1).text(),
                        range(self.table_mounts.rowCount())))

    @pyqtSlot()
    def setupETM(self):
        # fill values
        lcPort = app.adapterManager[0].lcPort
        self.lineEdit_lcport.setText(str(lcPort) if lcPort else "不可用")

        adapter = app.adapterManager[0]
        settings = adapter.backendSettings
        enabled = adapter.etmPid != 0
        if enabled:
            self.spinBox_dSpeedLimit.setValue(settings.downloadSpeedLimit)
            self.spinBox_uSpeedLimit.setValue(settings.uploadSpeedLimit)
            self.spinBox_maxRunningTasksNum.setValue(settings.maxRunTaskNumber)

            # connect signals
            self.accepted.connect(self.saveETM)
        else:
            self.spinBox_dSpeedLimit.setEnabled(False)
            self.spinBox_uSpeedLimit.setEnabled(False)
            self.spinBox_maxRunningTasksNum.setEnabled(False)

    @pyqtSlot()
    def saveETM(self):
        adapter = app.adapterManager[0]
        adapter.do_applySettings({
            "downloadSpeedLimit": self.spinBox_dSpeedLimit.value(),
            "uploadSpeedLimit": self.spinBox_uSpeedLimit.value(),
            "maxRunTaskNumber": self.spinBox_maxRunningTasksNum.value(),
        })
