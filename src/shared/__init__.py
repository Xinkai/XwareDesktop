# -*- coding: utf-8 -*-

import logging

__version__ = "0.9"

XWARE_VERSION = "1.0.21"

from collections import namedtuple
BackendInfo = namedtuple("BackendInfo", ["etmPid", "lcPort", "userId", "peerId"])
