# -*- coding: utf-8 -*-

import logging
from launcher import app

from PyQt5.QtCore import QObject, pyqtSlot

import re


# qqdl, flashget, thunder, http, ftp, https, ed2k, magnet
class UrlExtractor(QObject):
    _patterns = None

    def __init__(self, parent):
        super().__init__(parent)

        if app:
            app.applySettings.connect(self.slotSettingsChanged)
        else:
            pass  # unittest

    @pyqtSlot()
    def slotSettingsChanged(self):
        patternLines = app.settings.myGet("frontend", "watchpattern").split("\n")
        patternList = []
        for line in patternLines:
            if len(line) == 0 or line.startswith("//"):
                continue

            extensions = line.split(";")

            extensions = filter(lambda ext: ext != "",    # get rid of empty ext
                                map(lambda ext: ext[1:],  # get rid of wildcard
                                    extensions))

            patternList.extend(extensions)

        patternSet = set(patternList)
        self.updatePatternRegex(patternSet)

    def updatePatternRegex(self, patternSet):
        # http://www.w3.org/Addressing/URL/url-spec.txt

        patternStr = "|".join(patternSet).replace(".", "\.")

        # u3010 【
        # u3011 】

        self._patterns = re.compile(
            r"(?:(?:(?:"
            # match all private links
            r"(?:qqdl|flashget|thunder)://(?:[A-Za-z0-9+/=]{4})+"
            r")|(?:"  # http, ftp, https
            r"(?:http|ftp|https)://"                            # scheme
            r"(?:(?:[a-zA-Z0-9\-_\.\+]+)(?::[a-zA-Z0-9\-_\.\+]+)?@)?"  # username, password
            r"(?:[\w|\.|\-])+"                                  # host, also works for ip address
            r"(?::[0-9]{1,5})?/"                                # port, slash
            r"(?:[\w\.%=/&\-,()\u3010\u3011]+)" +               # path + filename
            r"(?:{})".format(patternStr) +                      # extension
            r"(?:\?(?:[\w\.\-\=\%\&\,\/])*)?"
            r")|(?:"
            # match all ed2k
            r"ed2k://"
            r"(?:\|file\|)"                                     # type -> file
            r"(?:[\w|_|\-|\.|%|&|'|\[|\]]+)\|"                  # filename
            r"(?:[0-9]+)\|"                                     # filesize
            r"(?:[a-f0-9]{32})\|"                               # hash
            r"(?:[\w|\/|\.|\-|:|\,|=]+)"                        # additional
            r")|(?:"
            r"magnet:\?[\w\.\=\:\&\+%\-\/]+"
            r"))(?:(?=[\s|#])|(?:$)))", re.I)

    def extract(self, text):
        # extract from a raw text, and return a list of supported links
        result = re.findall(self._patterns, text)
        return result
