# -*- coding: utf-8 -*-

import logging

import configparser, pickle, binascii
import types
from functools import partial


class ProxyAddons(object):
    def has(self, section, key):
        key = key.lower()
        return self.has_option(section, key)

    def set(self, section, key, value):
        key = key.lower()
        try:
            super(self.__class__, self).set(section, key, value)
        except configparser.NoSectionError:
            self.add_section(section)
            super(self.__class__, self).set(section, key, value)

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
        pickled = pickle.dumps(value, 4)  # protocol 4 requires Py3.4
        pickledBytes = binascii.hexlify(pickled)
        pickledStr = pickledBytes.decode("ascii")
        self.set(section, key, pickledStr)


class SettingsAccessorBase(configparser.ConfigParser):
    def __init__(self, configFilePath, defaults):
        super().__init__()
        self._loadAddons(target = self)
        self._configFilePath = configFilePath
        self._defaultDict = defaults
        self.read(self._configFilePath)

    def get(self, section, key, *args, **kwargs):
        assert not args
        assert not kwargs
        # override this, because we use fallback map
        key = key.lower()
        return super().get(section, key, fallback = self._defaultDict[section][key])

    def getint(self, section, key, *args, **kwargs):
        # override this, because super() version doesn't call overridden get()
        return int(self.get(section, key, *args, **kwargs))

    def getboolean(self, *args, **kwargs):
        raise NotImplementedError("use getbool")

    def save(self):
        with open(self._configFilePath, 'w', encoding = "UTF-8") as configfile:
            self.write(configfile)

    def _loadAddons(self, target, section = None):
        for name, func in ProxyAddons.__dict__.items():
            if name.startswith("__"):
                continue

            assert name not in target.__dict__, "{name} already in {target}".format(name = name,
                                                                                    target = target)

            methodTyped = types.MethodType(func, self)
            if not section:
                assert isinstance(target, self.__class__)
                setattr(target, name,
                        methodTyped)

            else:
                assert isinstance(target, configparser.SectionProxy)
                setattr(target, name,
                        partial(methodTyped, section))

        setattr(target, "addons_loaded", True)

    def __getitem__(self, section):
        result = super().__getitem__(section)
        if not getattr(result, "addons_loaded", False):
            self._loadAddons(target = result, section = section)
        return result
