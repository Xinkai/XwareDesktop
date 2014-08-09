# -*- coding: utf-8 -*-

# This file is a pure python library that aims to be an open-source implementation for
# yuancheng.xunlei.com javascript libraries.
# This file only depends on python standard libraries + aiohttp


import asyncio, aiohttp
from collections import namedtuple
from enum import IntEnum, unique

import json
from json.decoder import scanner, scanstring, JSONDecoder
from urllib.parse import unquote


class UnquotingJsonDecoder(JSONDecoder):
    # This class automatically unquotes URL-quoted characters like %20
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.parse_string = self.unquote_parse_string
        # "rebuild" scan_once
        # scanner.c_make_scanner doesn't seem to support custom parse_string.
        self.scan_once = scanner.py_make_scanner(self)

    @staticmethod
    def unquote_parse_string(*args, **kwargs):
        result = scanstring(*args, **kwargs)  # => (str, end_index)
        unquotedResult = (unquote(result[0]), result[1])
        return unquotedResult


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


class CLIENT_NONFATAL_ERROR(Exception):
    pass


class INVALID_OPTIONS_ERROR(CLIENT_NONFATAL_ERROR):
    pass


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


class XwareClient(object):
    def __init__(self):
        self._options = {
            "timeout": 1,
            "ua": "libxware/0.1",
        }
        self._connector = aiohttp.TCPConnector(share_cookies = True)

    def updateOptions(self, options):
        self._options.update(options)

    def _readyCheck(self):
        try:
            assert "host" in self._options
            assert 0 < int(self._options["port"]) <= 65535
        except (AssertionError, ValueError, KeyError):
            raise INVALID_OPTIONS_ERROR()

    @asyncio.coroutine
    def get(self, parts):
        self._readyCheck()
        res = yield from aiohttp.request(
            "GET",
            "http://{host}:{port}/{parts}".format(
                host = self._options["host"], port = self._options["port"], parts = parts),
            connector = self._connector)
        assert res.status == 200
        body = yield from res.read()
        return body

    @asyncio.coroutine
    def getJson(self, parts):
        content = yield from self.get(parts)
        res = content.decode("utf-8")
        return json.loads(res, cls = UnquotingJsonDecoder)

    @asyncio.coroutine
    def getJson2(self, parts):
        result = yield from self.getJson(parts)
        assert result["rtn"] == 0
        del result["rtn"]

        if "msg" in result:
            assert result["msg"] == ""
            del result["msg"]

        return result

    @asyncio.coroutine
    def get_getsysinfo(self):
        res = yield from self.getJson("getsysinfo")
        result = GetSysInfo(*res)
        assert result.Return == 0
        return result

    def get_list(self, klass, starting = 0, count = 999999, abs_path = True, fixed_id = False):
        assert isinstance(klass, TaskClass)
        result = self.getJson2("list?v=2&type={klass}&pos={starting}&number={count}&needUrl=1"
                               "&abs_path={abs_path}&fixed_id={fixed_id}"
                               .format(klass = int(klass),
                                       starting = starting,
                                       count = count,
                                       abs_path = int(abs_path),
                                       fixed_id = int(fixed_id)))

        return result

    def get_settings(self):
        result = self.getJson2("settings?v=2")
        return result

    @asyncio.coroutine
    def post(self, parts, *args, data = None):
        assert not args, args
        self._readyCheck()
        res = yield from aiohttp.request(
            "POST",
            "http://{host}:{port}/{parts}".format(
                host = self._options["host"], port = self._options["port"], parts = parts),
            data = data,
            connector = self._connector)
        assert res.status == 200
        body = yield from res.read()
        return body

    @asyncio.coroutine
    def postJson(self, parts, **kwargs):
        content = yield from self.post(parts, **kwargs)
        res = content.decode("utf-8")
        return json.loads(res, cls = UnquotingJsonDecoder)

    @asyncio.coroutine
    def postJsonP(self, parts, **kwargs):
        content = yield from self.post(parts, **kwargs)
        res = content.decode("utf-8")
        l = res.index("(") + 1
        r = res.rindex(")")
        res = res[l:r]  # get rid of jsonp
        return json.loads(res, cls = UnquotingJsonDecoder)

    @asyncio.coroutine
    def postJson2(self, parts, **kwargs):
        result = yield from self.postJson(parts, **kwargs)
        rtn = result["rtn"]
        assert rtn == 0, rtn
        del result["rtn"]
        return result

    @asyncio.coroutine
    def postJsonP2(self, parts, **kwargs):
        result = yield from self.postJsonP(parts, **kwargs)
        rtn = result["rtn"]
        assert rtn == 0, rtn
        del result["rtn"]
        return result

    @asyncio.coroutine
    def post_del(self, tasks: "iterable of id", recycle: bool, delete: bool):
        result = yield from self.postJson2("del?v=2&pid=ignore&tasks={tasks}&recycleTask={recycle}"
                                           "&deleteFile={delete}&callback=ignore&_=ignore"
                                           .format(tasks = ",".join(map(str(tasks))),
                                                   recycle = int(recycle),
                                                   delete = int(delete)))
        return result

    @asyncio.coroutine
    def post_settings(self, settings: dict):
        assert isinstance(settings, dict)
        params = []
        for key, value in settings.items():
            assert key in Settings._fields
            params.append("{k}={v}".format(k = key, v = value))
        result = yield from self.postJson2("settings?v=2&" + "&".join(params))
        return result

    @asyncio.coroutine
    def post_pause(self, tasks: "iterable of id"):
        result = yield from self.postJsonP2("pause?v=2&pid=ignore&tasks={tasks}&callback=ignore"
                                            .format(tasks = ",".join(map(str, tasks))))
        return result

    @asyncio.coroutine
    def post_start(self, tasks: "iterable of id"):
        result = yield from self.postJsonP2("start?v=2&pid=ignore&tasks={tasks}&callback=ignore"
                                            .format(tasks = ",".join(map(str, tasks))))
        return result

    @asyncio.coroutine
    def post_openLixianChannel(self, taskId: int, enable: bool):
        result = yield from self.postJsonP2("openLixianChannel?v=2&pid=ignore&taskid={taskId}&"
                                            "open={enable}&callback=ignore"
                                            .format(taskId = taskId,
                                                    enable = "true" if enable else "false"))
        return result

    @asyncio.coroutine
    def post_openVipChannel(self, taskId: int):
        result = yield from self.postJsonP2("openVipChannel?v=2&pid=ignore&taskid={taskId}&"
                                            "callback=ignore"
                                            .format(taskId = taskId))
        return result

    @asyncio.coroutine
    def post_urlCheck(self):
        pass

    @asyncio.coroutine
    def post_btCheck(self, filepath):
        # xware doesn't seem to support chunked uploading, which aiohttp always uses.
        # See the bug I opened: https://github.com/KeepSafe/aiohttp/issues/126
        files = {
            "file": open(filepath, 'rb'),
        }
        result = yield from self.postJsonP2(
            "urlCheck?v=2&pid=ignore&callback=ignore&type={urlCheckType}&upload=1".format(
                urlCheckType = int(UrlCheckType.BitTorrentFile)),
            data = files)

        return result

    @asyncio.coroutine
    def post_unbind(self):
        pass

    @asyncio.coroutine
    def post_bind(self):
        pass
