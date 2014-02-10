# -*- coding: utf-8 -*-
from PyQt5.QtCore import pyqtSlot

from PyQt5.QtWidgets import QDialog, QTableWidgetItem
from ui_settings import Ui_Dialog
import configparser
import constants

class SettingAccessor(object):
    def __init__(self):

        self.config = configparser.ConfigParser()
        self.config.read(constants.CONFIG_FILE)

    def get(self, section, key, fallback = None):
        return self.config.get(section, key, fallback = fallback)

    def set(self, section, key, value):
        try:
            self.config.set(section, key, value)
        except configparser.NoSectionError:
            self.config.add_section(section)
            self.config.set(section, key, value)

    def save(self):
        with open(constants.CONFIG_FILE, 'w') as configfile:
            self.config.write(configfile)

class SettingsDialog(QDialog, Ui_Dialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.window = parent
        self.setupUi(self)

        self.lineEdit_loginUsername.setText(settingsAccessor.get("account", "username"))
        self.lineEdit_loginPassword.setText(settingsAccessor.get("account", "password"))
        self.checkBox_autoLogin.setChecked(settingsAccessor.get("account", "autologin", "True") == "True")
        self.checkBox_enableDevelopersTools.setChecked(
            settingsAccessor.get("frontend", "enableDevelopersTools", "False") == "True")

        from PyQt5.QtWidgets import QButtonGroup
        self.btngrp_etmStartWhen = QButtonGroup()
        self.btngrp_etmStartWhen.addButton(self.radio_backendStartWhen1, 1)
        self.btngrp_etmStartWhen.addButton(self.radio_backendStartWhen2, 2)
        self.btngrp_etmStartWhen.addButton(self.radio_backendStartWhen3, 3)
        self.btngrp_etmStartWhen.button(int(settingsAccessor.get("xwared", "startETMWhen", "1"))).setChecked(True)

        self.rejected.connect(lambda: self.close())
        self.accepted.connect(self.writeSettings)

        # Mounts
        self.setupMounts()

    def setupMounts(self):
        self.btn_addMount.clicked.connect(self.slotAddMount)
        self.btn_removeMount.clicked.connect(self.slotRemoveMount)

        mountsMapping = self.window.mountsFaker.getMountsMapping()
        for i, item in enumerate(self.window.mountsFaker.mounts):
            self.table_mounts.insertRow(i)
            self.table_mounts.setItem(i, 0, QTableWidgetItem(item))
            self.table_mounts.setItem(i, 1, QTableWidgetItem(chr(ord('C') + i) + ":"))
            self.table_mounts.setItem(i, 2, QTableWidgetItem(mountsMapping.get(item, "无")))

    @pyqtSlot()
    def slotAddMount(self):
        import os
        from PyQt5.QtWidgets import QFileDialog
        from PyQt5.Qt import Qt

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
        settingsAccessor.set("account", "username", self.lineEdit_loginUsername.text())
        settingsAccessor.set("account", "password", self.lineEdit_loginPassword.text())
        settingsAccessor.set("account", "autologin", "True" if self.checkBox_autoLogin.isChecked() else "False")
        settingsAccessor.set("frontend", "enableDevelopersTools",
                                "True" if self.checkBox_enableDevelopersTools.isChecked() else "False")
        settingsAccessor.set("xwared", "startETMWhen", self.btngrp_etmStartWhen.id(self.btngrp_etmStartWhen.checkedButton()))
        settingsAccessor.save()

        self.window.mountsFaker.setMounts(self.newMounts)

    @property
    def newMounts(self):
        return list(map(lambda row: self.table_mounts.item(row, 0).text(),
                        range(self.table_mounts.rowCount())))
settingsAccessor = None