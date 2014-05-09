# -*- coding: utf-8 -*-

from launcher import app

from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtWidgets import QDialog, QTableWidgetItem, QButtonGroup, QFileDialog
from PyQt5.QtGui import QBrush

import os, re, subprocess

import constants
from etmpy import EtmSetting
from .ui_settings import Ui_Dialog


class SettingsDialog(QDialog, Ui_Dialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.setupUi(self)

        self.lineEdit_loginUsername.setText(app.settings.get("account", "username"))
        self.lineEdit_loginPassword.setText(app.settings.get("account", "password"))
        self.checkBox_autoLogin.setChecked(app.settings.getbool("account", "autologin"))
        self.checkBox_autoStartFrontend.setChecked(self.doesAutoStartFileExists())

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
        self.btngrp_etmStartWhen.button(app.settings.getint("xwared", "startetmwhen")) \
            .setChecked(True)

        self.btn_addMount.clicked.connect(self.slotAddMount)
        self.btn_removeMount.clicked.connect(self.slotRemoveMount)
        self.btn_refreshMount.clicked.connect(self.setupMounts)

        # Mounts
        self.setupMounts()

        # backend setting is a different thing!
        self.setupETM()

    @staticmethod
    def doesAutoStartFileExists():
        return os.path.lexists(constants.FRONTEND_AUTOSTART_FILE)

    @staticmethod
    def permissionCheck():
        ansiEscape = re.compile(r'\x1b[^m]*m')

        with subprocess.Popen([constants.PERMISSIONCHECK],
                              stdout = subprocess.PIPE,
                              stderr = subprocess.PIPE) as proc:
            output = proc.stdout.read().decode("utf-8")
            output = ansiEscape.sub('', output)
            lines = output.split("\n")

        prevLine = None
        currMount = None
        result = {}
        for line in lines:
            if len(line.strip()) == 0:
                continue

            if all(map(lambda c: c == '=', line)):
                if currMount:
                    result[currMount] = result[currMount][:-1]

                result[prevLine] = []
                currMount = prevLine
                continue

            if currMount:
                if line != "正常。":
                    result[currMount].append(line)

            prevLine = line

        return result

    @pyqtSlot(int)
    def slotWatchClipboardToggled(self, state):
        # disable pattern settings, before
        # 1. complete patterns
        # 2. test glib key file compatibility
        self.plaintext_watchPattern.setReadOnly(True)
        self.plaintext_watchPattern.setEnabled(state)

    @pyqtSlot()
    def setupMounts(self):
        self.table_mounts.setRowCount(0)
        self.table_mounts.clearContents()

        permissionCheckResult = self.permissionCheck()
        permissionCheckFailed = ["无法获得检测权限。运行/opt/xware_desktop/permissioncheck查看原因。"]

        mountsMapping = app.mountsFaker.getMountsMapping()
        for i, mount in enumerate(app.mountsFaker.mounts):
            # mounts = ['/path/to/1', 'path/to/2', ...]
            self.table_mounts.insertRow(i)
            self.table_mounts.setItem(i, 0, QTableWidgetItem(mount))
            # drive1: the drive letter it should map to, by alphabetical order
            drive1 = chr(ord('C') + i) + ":"
            self.table_mounts.setItem(i, 1, QTableWidgetItem(drive1))
            # drive2: the drive letter it actually is assigned to
            drive2 = mountsMapping.get(mount, "无")

            # check 1: permission
            errors = permissionCheckResult.get(mount, permissionCheckFailed)

            # check 2: mapping
            if drive1 != drive2:
                errors.append(
                    "警告：盘符映射在'{actual}'，而不是'{should}'。需要重启后端修复。".format(
                        actual = drive2,
                        should = drive1))

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
            self.table_mounts.setItem(row, 0, QTableWidgetItem(selected))
            self.table_mounts.setItem(row, 1, QTableWidgetItem("新近添加"))
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
        doesAutoStartFileExists = self.doesAutoStartFileExists()
        if self.checkBox_autoStartFrontend.isChecked() and not doesAutoStartFileExists:
            # mkdir if autostart dir doesn't exist
            try:
                os.mkdir(os.path.dirname(constants.FRONTEND_AUTOSTART_FILE))
            except OSError:
                pass  # already exists
            os.symlink(constants.DESKTOP_FILE_LOCATION,
                       constants.FRONTEND_AUTOSTART_FILE)
        elif (not self.checkBox_autoStartFrontend.isChecked()) and doesAutoStartFileExists:
            os.remove(constants.FRONTEND_AUTOSTART_FILE)

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
        # app.settings.set("frontend", "watchpattern",
        #                         self.plaintext_watchPattern.toPlainText())
        app.settings.setint("xwared", "startetmwhen",
                            self.btngrp_etmStartWhen.id(self.btngrp_etmStartWhen.checkedButton()))

        startETMWhen = app.settings.getint("xwared", "startetmwhen")
        if startETMWhen == 1:
            app.settings.setbool("xwared", "startetm", True)

        app.settings.save()

        app.mountsFaker.mounts = self.newMounts
        app.settings.applySettings.emit()
        super().accept()

    @property
    def newMounts(self):
        return list(map(lambda row: self.table_mounts.item(row, 0).text(),
                        range(self.table_mounts.rowCount())))

    @pyqtSlot()
    def setupETM(self):
        # fill values
        self.lineEdit_lcport.setText(app.etmpy.cfg.get("local_control.listen_port", "不可用"))

        etmSettings = app.etmpy.getSettings()
        if etmSettings:
            self.spinBox_dSpeedLimit.setValue(etmSettings.dLimit)
            self.spinBox_uSpeedLimit.setValue(etmSettings.uLimit)
            self.spinBox_maxRunningTasksNum.setValue(etmSettings.maxRunningTasksNum)

            # connect signals
            self.accepted.connect(self.saveETM)
        else:
            self.spinBox_dSpeedLimit.setEnabled(False)
            self.spinBox_uSpeedLimit.setEnabled(False)
            self.spinBox_maxRunningTasksNum.setEnabled(False)

    @pyqtSlot()
    def saveETM(self):
        newsettings = EtmSetting(dLimit = self.spinBox_dSpeedLimit.value(),
                                 uLimit = self.spinBox_uSpeedLimit.value(),
                                 maxRunningTasksNum = self.spinBox_maxRunningTasksNum.value())

        app.etmpy.saveSettings(newsettings)
