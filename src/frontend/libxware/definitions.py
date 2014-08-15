# -*- coding: utf-8 -*-

from enum import IntEnum, unique
from collections import namedtuple


@unique
class TaskClass(IntEnum):
    RUNNING = 0
    COMPLETED = 1
    RECYCLED = 2
    FAILED_ON_SUBMISSION = 3


@unique
class TaskState(IntEnum):
    DOWNLOADING = 0
    WAITING = 8
    STOPPED = 9
    PAUSED = 10
    FINISHED = 11
    FAILED = 12
    UPLOADING = 13
    SUBMITTING = 14
    DELETED = 15
    RECYCLED = 16
    SUSPENDED = 37
    ERROR = 38


@unique
class UrlCheckType(IntEnum):
    Url = 1  # ed2k/magnet/http ...
    BitTorrentFile = 2


# see definitions http://g.xunlei.com/forum.php?mod=viewthread&tid=30
GetSysInfo = namedtuple("GetSysInfo", ["Return",  # 0 -> success
                                       "Network",  # 1 -> ok
                                       "unknown1",
                                       "Bound",  # 1 -> bound
                                       "ActivateCode",  # str if Bound is 0 else ''
                                       "Mount",  # 1 -> ok
                                       "InternalVersion",
                                       "Nickname",
                                       "unknown2",
                                       "UserId",
                                       "unknown3"])


Settings = namedtuple("Settings", ['autoOpenVip',
                                   'slEndTime',
                                   'uploadSpeedLimit',
                                   'autoOpenLixian',
                                   'slStartTime',
                                   'autoDlSubtitle',
                                   'maxRunTaskNumber',
                                   'downloadSpeedLimit'])


@unique
class LixianChannelState(IntEnum):
    NOTUSED = 0
    SUBMITTING = 1
    DOWNLOADING = 2
    ACTIVATED = 3
    FAILED = 4


@unique
class VipChannelState(IntEnum):
    NOTUSED = 0
    SUBMITTING = 1
    ACTIVATED = 2
    FAILED = 3
