# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QDialog
from ui_settings import Ui_Dialog
import constants

class SettingAccessor(object):
    def __init__(self):
        import configparser
        self.config = configparser.ConfigParser()
        self.config.read(constants.CONFIG_FILE)

    def get(self, section, key, fallback = None):
        return self.config.get(section, key, fallback = fallback)

    def set(self, section, key, value):
        self.config.set(section, key, value)

    def save(self):
        with open(constants.CONFIG_FILE, 'w') as configfile:
            self.config.write(configfile)

class SettingsDialog(QDialog, Ui_Dialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.loadMountsSymLinks()

        self.lineEdit_loginUsername.setText(settingsAccessor.get("account", "username"))
        self.lineEdit_loginPassword.setText(settingsAccessor.get("account", "password"))
        self.checkBox_autoLogin.setChecked(settingsAccessor.get("account", "autologin", "True") == "True")
        self.checkBox_enableDevelopersTools.setChecked(
            settingsAccessor.get("frontend", "enableDevelopersTools", "False") == "True")

        self.rejected.connect(lambda: self.close())
        self.accepted.connect(self.writeSettings)

    def writeSettings(self):
        settingsAccessor.set("account", "username", self.lineEdit_loginUsername.text())
        settingsAccessor.set("account", "password", self.lineEdit_loginPassword.text())
        settingsAccessor.set("account", "autologin", "True" if self.checkBox_autoLogin.isChecked() else "False")
        settingsAccessor.set("frontend", "enableDevelopersTools",
                                "True" if self.checkBox_enableDevelopersTools.isChecked() else "False")

        settingsAccessor.save()

    def loadMountsSymLinks(self):
        import os
        from PyQt5.QtWidgets import QTableWidgetItem
        for i, drive in enumerate(os.listdir("/tmp/thunder/volumes")):
            print(i, drive, os.path.realpath("/tmp/thunder/volumes/" + drive))
            self.table_mounts.insertRow(i)
            self.table_mounts.setItem(i, 0, QTableWidgetItem(os.path.realpath("/tmp/thunder/volumes/" + drive)))
            self.table_mounts.setItem(i, 1, QTableWidgetItem(drive))
            self.table_mounts.setItem(i, 2, QTableWidgetItem("TODO"))

settingsAccessor = None