# -*- coding: utf-8 -*-

import logging

import configparser, pickle, binascii


class SettingsAccessorBase(object):
    def __init__(self, configFilePath, defaultDict, **kwargs):
        super().__init__()
        self.config = configparser.ConfigParser()
        self._configFilePath = configFilePath
        self._defaultDict = defaultDict
        self.config.read(self._configFilePath)

    def has(self, section, key):
        key = key.lower()
        return self.config.has_option(section, key)

    def get(self, section, key):
        key = key.lower()
        return self.config.get(section, key, fallback = self._defaultDict[section][key])

    def set(self, section, key, value):
        key = key.lower()
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
        pickled = pickle.dumps(value, 3)  # protocol 3 requires Py3.0
        pickledBytes = binascii.hexlify(pickled)
        pickledStr = pickledBytes.decode("ascii")
        self.set(section, key, pickledStr)

    def save(self):
        with open(self._configFilePath, 'w', encoding = "UTF-8") as configfile:
            self.config.write(configfile)
