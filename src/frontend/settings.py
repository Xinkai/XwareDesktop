# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QDialog
from ui_settings import Ui_Dialog

class SettingAccessor(object):
    __config_file__ = "/opt/xware_desktop/settings"
    def __init__(self):
        import configparser
        self.config = configparser.ConfigParser()
        self.config.read(self.__class__.__config_file__)

    def get(self, section, key, fallback = None):
        return self.config.get(section, key, fallback = fallback)

    def set(self, section, key, value):
        self.config.set(section, key, value)

    def save(self):
        with open(self.__class__.__config_file__, 'w') as configfile:
            self.config.write(configfile)

class SettingsDialog(QDialog, Ui_Dialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.lineEdit_loginUsername.setText(settingsAccessor.get("account", "username"))
        self.lineEdit_loginPassword.setText(settingsAccessor.get("account", "password"))

        self.rejected.connect(lambda: self.close())
        self.accepted.connect(self.writeSettings)

    def writeSettings(self):
        settingsAccessor.set("account", "username", self.lineEdit_loginUsername.text())
        settingsAccessor.set("account", "password", self.lineEdit_loginPassword.text())

        settingsAccessor.save()

settingsAccessor = None