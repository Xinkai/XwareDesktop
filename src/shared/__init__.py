# -*- coding: utf-8 -*-

import logging
from enum import IntEnum, unique

__version__ = "0.12"

XWARE_VERSION = "1.0.27"

XWARED_API_VERSION = 1


@unique
class XwaredSocketError(IntEnum):
    OK = 0
    SERVER_NO_METHOD = 1
    SERVER_EVALUATION = 2
    SERVER_UNKNOWN = 3
    CLIENT_CONNECTION_REFUSED = 4
    CLIENT_SOCKET_NOT_FOUND = 5
    CLIENT_UNKNOWN = 6
