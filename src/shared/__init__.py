# -*- coding: utf-8 -*-

import logging

__version__ = "0.10"

XWARE_VERSION = "1.0.26"

from collections import namedtuple
BackendInfo = namedtuple("BackendInfo", ["etmPid", "lcPort", "userId", "peerId"])
