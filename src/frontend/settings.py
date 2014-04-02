# -*- coding: utf-8 -*-

from PyQt5.QtCore import pyqtSlot, pyqtSignal, QObject, Qt
from PyQt5.QtWidgets import QDialog, QTableWidgetItem

import pickle, binascii

from ui_settings import Ui_Dialog
import configparser, os
import constants
import DistroDependent

DEFAULT_SETTINGS = {
    "account": {
        "username": None,
        "password": None,
        "autologin": True,
        "autostartlocation": os.path.expanduser("~/.config/autostart/xware-desktop.desktop"),
    },
    "frontend": {
        "enabledeveloperstools": False,
        "allowflash": True,
        "minimizetosystray": True,
        "closetominimize": False,
        "popnotifications": True,
        "notifybysound": True,
        "cachelocation": os.path.expanduser("~/.xware-desktop/cache/webkit"),
        "showmonitorwindow": True,
        "monitorfullspeed": 512,
        "watchclipboard": True,
        "watchpattern":
"""; 试验功能，暂不允许更改此设置
; packages
*.zip;*.tar;*.tgz;*.tar.gz;*.tbz;*.tbz2;*.tb2;*.tar.bz2;*.taz;*.tar.Z;*.tlz;*.tar.lz;*.tar.lzma;*.txz;*.tar.xz;*.cab;*.rar;*.7z;*.iso;*.dmg;*.img;

; documents
*.pdf;*.doc;*.docx;*.docm;*.xlt;*.xltx;*.xlsm;*.ppt;*.pptx;*.pptm;

; audio
*.mp1;*.mp2;*.mp3;*.mp4;*.flac;*.ape;*.webm;*.ogg;*.wav;*.wv;*.wma;*.aac;*.m4a;*.ra

; video
*.mp4;*.mkv;*.rm;*.rmvb;*.avi;*.flv;*.3gp;*.3g2;*.wmv;*.mov;*.vob

; media-related
*.srt;*.cue;*.m3u;*.sub

; programming
*.jar;*.apk;

; Linux
*.deb;*.rpm

; Windows
*.exe;*.msi;

; Mac

; misc
*.rom;*.ttf;*.bin;*.torrent
""",
        "mainwingeometry": None,
        "monitorwingeometry": None,
    },
    "xwared": {
        "startetm": True,
        "startetmwhen": 1
    },
    "scheduler": {
        "poweroffcmd": "",
        "hybridsleepcmd": "",
        "hibernatecmd": "",
        "suspendcmd": "",
    },
}

class SettingsAccessor(QObject):
    applySettings = pyqtSignal()

    app = None
    def __init__(self, app):
        super().__init__()
        self.config = configparser.ConfigParser()
        self.config.read(constants.CONFIG_FILE)
        self.app = app
        self.app.aboutToQuit.connect(self.save)

    def has(self, section, key):
        return self.config.has_option(section, key)

    def get(self, section, key):
        return self.config.get(section, key, fallback = DEFAULT_SETTINGS[section][key])

    def set(self, section, key, value):
        try:
            self.config.set(section, key, value)
        except configparser.NoSectionError:
            self.config.add_section(section)
            self.config.set(section, key, value)

    def getint(self, section, key):
        return int(self.get(section, key))

    def setint(self, section, key, value):
        assert type(value) is int
        self.set(section, key, str(value))

    def getbool(self, section, key):
        return True if self.get(section, key) in ("1", True) else False

    def setbool(self, section, key, value):
        assert type(value) is bool
        self.set(section, key, "1" if value else "0")

    def getobj(self, section, key):
        pickledStr = self.get(section, key)
        if type(pickledStr) is str and len(pickledStr) > 0:
            pickledBytes = pickledStr.encode("ascii")
            pickled = binascii.unhexlify(pickledBytes)
            unpickled = pickle.loads(pickled)
            return unpickled
        else:
            return pickledStr

    def setobj(self, section, key, value):
        pickled = pickle.dumps(value, 3) # protocol 3 requires Py3.0
        pickledBytes = binascii.hexlify(pickled)
        pickledStr = pickledBytes.decode("ascii")
        self.set(section, key, pickledStr)

    def save(self):
        with open(constants.CONFIG_FILE, 'w') as configfile:
            self.config.write(configfile)

class SettingsDialog(QDialog, Ui_Dialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowModality(Qt.WindowModal)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.app = parent.app
        self.setupUi(self)

        self.lineEdit_loginUsername.setText(self.settings.get("account", "username"))
        self.lineEdit_loginPassword.setText(self.settings.get("account", "password"))
        self.checkBox_autoLogin.setChecked(self.settings.getbool("account", "autologin"))
        self.checkBox_autoStartFrontend.setChecked(self.autoStartFileExists())

        self.checkBox_enableDevelopersTools.setChecked(
            self.settings.getbool("frontend", "enabledeveloperstools"))
        self.checkBox_allowFlash.setChecked(self.settings.getbool("frontend", "allowflash"))
        self.checkBox_minimizeToSystray.setChecked(self.settings.getbool("frontend", "minimizetosystray"))
        self.checkBox_closeToMinimize.setChecked(self.settings.getbool("frontend", "closetominimize"))
        self.checkBox_popNotifications.setChecked(self.settings.getbool("frontend", "popnotifications"))
        self.checkBox_notifyBySound.setChecked(self.settings.getbool("frontend", "notifybysound"))
        self.checkBox_showMonitorWindow.setChecked(self.settings.getbool("frontend", "showmonitorwindow"))
        self.spinBox_monitorFullSpeed.setValue(self.settings.getint("frontend", "monitorfullspeed"))
        # clipboard related
        self.checkBox_watchClipboard.stateChanged.connect(self.slotWatchClipboardToggled)
        self.checkBox_watchClipboard.setChecked(self.settings.getbool("frontend", "watchclipboard"))
        self.slotWatchClipboardToggled(self.checkBox_watchClipboard.checkState())
        self.plaintext_watchPattern.setPlainText(self.settings.get("frontend", "watchpattern"))

        from PyQt5.QtWidgets import QButtonGroup
        self.btngrp_etmStartWhen = QButtonGroup()
        self.btngrp_etmStartWhen.addButton(self.radio_backendStartWhen1, 1)
        self.btngrp_etmStartWhen.addButton(self.radio_backendStartWhen2, 2)
        self.btngrp_etmStartWhen.addButton(self.radio_backendStartWhen3, 3)
        self.btngrp_etmStartWhen.button(self.settings.getint("xwared", "startetmwhen")).setChecked(True)

        self.accepted.connect(self.writeSettings)

        self.btn_addMount.clicked.connect(self.slotAddMount)
        self.btn_removeMount.clicked.connect(self.slotRemoveMount)
        self.btn_refreshMount.clicked.connect(self.setupMounts)

        # Mounts
        self.setupMounts()

        # backend setting is a different thing!
        self.setupETM()

    # shorthand
    @property
    def settings(self):
        return self.app.settings
    # shorthand ends

    def autoStartFileExists(self):
        return os.path.lexists(self.settings.get("account", "autostartlocation"))

    @staticmethod
    def permissionCheck():
        import re
        ansiEscape = re.compile(r'\x1b[^m]*m')

        import subprocess
        with subprocess.Popen([constants.PERMISSIONCHECK], stdout = subprocess.PIPE, stderr = subprocess.PIPE) as proc:
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

        PermissionError = self.permissionCheck()

        mountsMapping = self.app.mountsFaker.getMountsMapping()
        for i, mount in enumerate(self.app.mountsFaker.mounts):
            # mounts = ['/path/to/1', 'path/to/2', ...]
            self.table_mounts.insertRow(i)
            self.table_mounts.setItem(i, 0, QTableWidgetItem(mount))
            drive1 = chr(ord('C') + i) + ":" # the drive letter it should map to, by alphabetical order
            self.table_mounts.setItem(i, 1, QTableWidgetItem(drive1))
            drive2 = mountsMapping.get(mount, "无") # the drive letter it actually is assigned to

            # check 1: permission
            errors = PermissionError.get(mount, ["无法获得检测权限。运行/opt/xware_desktop/permissioncheck查看原因。"])

            # check 2: mapping
            if drive1 != drive2:
                errors.append("警告：盘符映射在'{actual}'，而不是'{should}'。需要重启后端修复。".format(actual = drive2, should = drive1))

            from PyQt5.QtGui import QBrush

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
        import os
        from PyQt5.QtWidgets import QFileDialog

        fileDialog = QFileDialog(self, Qt.Dialog)
        fileDialog.setFileMode(QFileDialog.Directory)
        fileDialog.setOption(QFileDialog.ShowDirsOnly, True)
        fileDialog.setViewMode(QFileDialog.List)
        fileDialog.setDirectory(os.environ["HOME"])
        if (fileDialog.exec()):
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
    def writeSettings(self):
        self.settings.set("account", "username", self.lineEdit_loginUsername.text())
        self.settings.set("account", "password", self.lineEdit_loginPassword.text())
        self.settings.setbool("account", "autologin", self.checkBox_autoLogin.isChecked())
        autoStartFileExists = self.autoStartFileExists()
        if self.checkBox_autoStartFrontend.isChecked() and not autoStartFileExists:
            os.symlink(constants.DESKTOP_FILE_LOCATION, self.settings.get("account", "autostartlocation"))
        elif (not self.checkBox_autoStartFrontend.isChecked()) and autoStartFileExists:
            os.remove(self.settings.get("account", "autostartlocation"))

        self.settings.setbool("frontend", "enabledeveloperstools",
                                self.checkBox_enableDevelopersTools.isChecked())
        self.settings.setbool("frontend", "allowflash",
                                self.checkBox_allowFlash.isChecked())
        self.settings.setbool("frontend", "minimizetosystray",
                                self.checkBox_minimizeToSystray.isChecked())

        # A possible Qt bug
        # https://bugreports.qt-project.org/browse/QTBUG-37695
        self.settings.setbool("frontend", "closetominimize",
                                self.checkBox_closeToMinimize.isChecked())
        self.settings.setbool("frontend", "popnotifications",
                                self.checkBox_popNotifications.isChecked())
        self.settings.setbool("frontend", "notifybysound",
                                self.checkBox_notifyBySound.isChecked())

        self.settings.setbool("frontend", "showmonitorwindow",
                                self.checkBox_showMonitorWindow.isChecked())
        self.settings.setint("frontend", "monitorfullspeed",
                                self.spinBox_monitorFullSpeed.value())
        self.settings.setbool("frontend", "watchclipboard",
                                self.checkBox_watchClipboard.isChecked())
        # self.settings.set("frontend", "watchpattern",
        #                         self.plaintext_watchPattern.toPlainText())
        self.settings.setint("xwared", "startetmwhen",
                          self.btngrp_etmStartWhen.id(self.btngrp_etmStartWhen.checkedButton()))

        startETMWhen = self.settings.getint("xwared", "startetmwhen")
        if startETMWhen == 1:
            self.settings.setbool("xwared", "startetm", True)

        self.settings.save()

        self.app.mountsFaker.setMounts(self.newMounts)
        self.settings.applySettings.emit()

    @property
    def newMounts(self):
        return list(map(lambda row: self.table_mounts.item(row, 0).text(),
                        range(self.table_mounts.rowCount())))

    @pyqtSlot()
    def setupETM(self):
        etmpy = self.app.etmpy

        # fill values
        self.lineEdit_lcport.setText(etmpy.cfg.get("local_control.listen_port", "不可用"))

        etmSettings = etmpy.getSettings()
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
        import etmpy

        newsettings = etmpy.EtmSetting(dLimit = self.spinBox_dSpeedLimit.value(),
                                       uLimit = self.spinBox_uSpeedLimit.value(),
                                       maxRunningTasksNum = self.spinBox_maxRunningTasksNum.value())

        self.app.etmpy.saveSettings(newsettings)
