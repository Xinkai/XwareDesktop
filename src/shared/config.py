# -*- coding: utf-8 -*-

import logging

import configparser, pickle, binascii
import types
from functools import partial
from collections import MutableMapping


class ProxyAddons(object):
    def has(self, section, key):
        key = key.lower()
        try:
            self.get(section, key)
            return True
        except KeyError:
            return False

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

    def setfloat(self, section, key, value):
        assert type(value) in (int, float)
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
        pickled = pickle.dumps(value, pickle.HIGHEST_PROTOCOL)
        pickledBytes = binascii.hexlify(pickled)
        pickledStr = pickledBytes.decode("ascii")
        self.set(section, key, pickledStr)


class FallbackSectionProxy(MutableMapping):
    def __init__(self, parser, name):
        self._parser = parser
        self._name = name

    def __getattr__(self, item):
        parserMember = getattr(self._parser, item, None)
        if isinstance(parserMember, types.MethodType):
            return partial(parserMember, self._name)
        raise AttributeError("Cannot find {}".format(item))

    @property
    def name(self):
        return self._name

    # Implement Abstract Members
    def __iter__(self):
        raise NotImplementedError()

    def __setitem__(self, key, value):
        self._parser.set(self._name, key, value)

    def __getitem__(self, key):
        return self._parser.get(self._name, key)

    def __delitem__(self, key):
        raise NotImplementedError()

    def __len__(self):
        raise NotImplementedError()


class SettingsAccessorBase(configparser.ConfigParser):
    def __init__(self, configFilePath, defaults):
        super().__init__()
        self._loadAddons(target = self)
        self._configFilePath = configFilePath
        self._defaultDict = defaults
        self.read(self._configFilePath, encoding = "UTF-8")

    def get(self, section, key, *args, **kwargs):
        assert not args
        # TODO: disable the next line because otherwise won't work with SectionProxy
        # assert not kwargs
        # override this, because we use fallback map
        key = key.lower()
        try:
            return super().get(section, key)
        except (configparser.NoOptionError, configparser.NoSectionError):
            return self._defaultDict[section][key]

    def getint(self, section, key, *args, **kwargs):
        # override this, because super() version doesn't call overridden get()
        return int(self.get(section, key, *args, **kwargs))

    def getfloat(self, section, key, *args, **kwargs):
        return float(self.get(section, key, *args, **kwargs))

    def getboolean(self, *args, **kwargs):
        raise NotImplementedError("use getbool")

    def save(self):
        with open(self._configFilePath, 'w', encoding = "UTF-8") as configfile:
            self.write(configfile)

    def _loadAddons(self, target, section = None):
        if section:
            assert isinstance(target, configparser.SectionProxy)
        else:
            assert isinstance(target, self.__class__)

        for name, func in ProxyAddons.__dict__.items():
            if name.startswith("__"):
                continue

            assert name not in target.__dict__, "{name} already in {target}".format(name = name,
                                                                                    target = target)

            methodTyped = types.MethodType(func, self)
            if not section:
                setattr(target, name, methodTyped)
            else:
                setattr(target, name, partial(methodTyped, section))

        if section:
            #   If a section not in the file, FallbackSectionProxy will be used.
            # It is implemented in self.__getitem__.
            #   But when only part of the section is written to the file, the builtin
            # SectionProxy is used. It has no knowledge about the fallback dict.
            #   Here we monkey patch SectionProxy, so that it will find keys from fallback dict.
            #   Also, should be noted that __magicmethod__ needs to patched to the __class__,
            # not the instance.
            targetClass = target.__class__

            def _enableFallback(SELF, key):
                return SELF._parser.get(SELF._name, key)

            if not hasattr(targetClass, "FALLBACK_PATCHED"):
                setattr(targetClass, "__getitem__", _enableFallback)
                setattr(targetClass, "FALLBACK_PATCHED", True)

        setattr(target, "addons_loaded", True)

    def __getitem__(self, section: str):
        try:
            result = super().__getitem__(section)
        except KeyError as e:
            if section in self._defaultDict:
                proxy = FallbackSectionProxy(self, section)
                if section not in self._proxies:
                    self._proxies[section] = proxy
                return proxy
            else:
                raise e
        if not getattr(result, "addons_loaded", False):
            self._loadAddons(target = result, section = section)
        return result

    def itr_sections_with_prefix(self, prefix):
        sections = self.sections()
        defaultSections = self._defaultDict.keys()

        allSections = set(sections) | set(defaultSections)
        for section in allSections:
            if section.startswith(prefix):
                yield section, self[section]
