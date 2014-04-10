# -*- coding: utf-8 -*-

import logging

from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.QtWidgets import QApplication
import re


# qqdl, flashget, thunder, http, ftp, https, ed2k, magnet
class UrlExtractor(QObject):
    _patterns = None
    actionsQueue = None
    _app = None

    def __init__(self, actionsQueue):
        super().__init__(actionsQueue)
        self.actionsQueue = actionsQueue

        self._app = QApplication.instance()
        if self._app:
            self._app.settings.applySettings.connect(self.slotSettingsChanged)
        else:
            pass  # unittest

    @pyqtSlot()
    def slotSettingsChanged(self):
        patternLines = self._app.settings.get("frontend", "watchpattern").split("\n")
        patternList = []
        for line in patternLines:
            if len(line) == 0 or line[0] == ";":
                continue

            extensions = line.split(";")

            extensions = filter(lambda ext: ext != "",    # get rid of empty ext
                                map(lambda ext: ext[1:],  # get rid of wildcard
                                    extensions))

            patternList.extend(extensions)

        patternSet = set(patternList)
        self.updatePatternRegex(patternSet)

    def updatePatternRegex(self, patternSet):
        patternStr = "|".join(patternSet)
        print("updated clipboard pattern regex", patternStr)

        self._patterns = re.compile(
            r"(?:"
            # match all private links
            r"(?:qqdl|flashget|thunder)://(?:[A-Za-z0-9+/=]{4})+"
            r")|(?:"  # http, ftp, https
            r"(?:http|ftp|https)://"                            # scheme
            r"(?:(?:[\w]+)(?:\:[\w]+)?@)?"                      # username, password
            r"(?:[\w|.|\-]+)"                                   # host, also works for ip address
            r"(?:\:[0-9]{1,5})?/"                               # port, slash
            r"(?:[\w.%=\/&\-\,\(\)])+" +                        # path + filename
            r"(?:{})".format(patternStr) +                      # extension
            r"(?:(?:\?[\w.\-=%&,\/]*)|(?= |\r|\n|\t|))"
            r")|(?:"
            # match all ed2k
            r"ed2k://"
            r"(?:\|file\|)"                                     # type -> file
            r"(?:[\w|_|\-|.|%]+)\|"                             # filename
            r"(?:[0-9]+)\|"                                     # filesize
            r"(?:[a-f0-9]{32})\|"                               # hash
            r"(?:(?:[\w|\/|.|\-|:|\,|=]+)|(?= |\r|\n|\t|))"     # additional
            r")|(?:"
            r"magnet:\?[\w|\.|\=|\:|\&|\+|%|\-|\/]+"
            r")", re.I)

    def extract(self, text):
        # extract from a raw text, and return a list of supported links
        result = re.findall(self._patterns, text)
        print("extracted urls", result)
        return result
