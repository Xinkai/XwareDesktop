# -*- coding: utf-8 -*-

import logging
from enum import IntEnum, unique

__version__ = "0.12"

XWARE_VERSION = "1.0.30"

DATE = 20140813


@unique
class XwaredSocketError(IntEnum):
    SERVER_OK = 0x00
    SERVER_DECODE = 0x01
    SERVER_JSON_LOAD = 0x02
    SERVER_NO_METHOD = 0x03
    SERVER_NO_ARGUMENTS = 0x04
    SERVER_EVALUATION = 0x05
    SERVER_UNKNOWN = 0xFF

    CLIENT_OK = 0x0100
    CLIENT_CONNECTION_REFUSED = 0x0200
    CLIENT_SOCKET_NOT_FOUND = 0x0300
    CLIENT_DECODE = 0x400
    CLIENT_JSON_LOAD = 0x500
    CLIENT_UNKNOWN = 0xFF00
