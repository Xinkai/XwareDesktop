# -*- coding: utf-8 -*-

# This file is a pure python library that aims to be an open-source implementation for
# yuancheng.xunlei.com javascript libraries.
# This file only depends on python standard libraries + aiohttp


import asyncio, aiohttp
from collections import OrderedDict
import json
from json.decoder import scanner, scanstring, JSONDecoder
from urllib.parse import unquote

from .definitions import GetSysInfo, TaskClass, Settings, UrlCheckType


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


class CLIENT_NONFATAL_ERROR(Exception):
    pass


class INVALID_OPTIONS_ERROR(CLIENT_NONFATAL_ERROR):
    pass


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
            if "host" not in self._options:
                raise ValueError("No host")
            if not 0 < int(self._options["port"]) <= 65535:
                raise ValueError("No port")
        except (ValueError, KeyError):
            raise INVALID_OPTIONS_ERROR()

    @asyncio.coroutine
    def get(self, path, params = None, data = None):
        self._readyCheck()
        res = yield from aiohttp.request(
            "GET",
            "http://{host}:{port}/{path}".format(
                host = self._options["host"], port = self._options["port"], path = path),
            connector = self._connector,
            params = params,
            data = data,
        )
        if not res.status == 200:
            raise ValueError("response status is not 200", res.status)
        body = yield from res.read()
        return body

    @asyncio.coroutine
    def getJson(self, *args, **kwargs):
        content = yield from self.get(*args, **kwargs)
        res = content.decode("utf-8")
        return json.loads(res, cls = UnquotingJsonDecoder)

    @asyncio.coroutine
    def getJson2(self, *args, **kwargs):
        result = yield from self.getJson(*args, **kwargs)
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
        result = self.getJson2(
            "list",
            params = OrderedDict([
                ("v", 2),
                ("type", int(klass)),
                ("pos", starting),
                ("number", count),
                ("needUrl", int(True)),
                ("abs_path", int(abs_path)),
                ("fixed_id", int(fixed_id)),
            ]),
        )
        return result

    def get_settings(self):
        result = self.getJson2(
            "settings",
            params = OrderedDict([
                ("v", 2)
            ]),
        )
        return result

    @asyncio.coroutine
    def post(self, path, params = None, data = None):
        self._readyCheck()
        res = yield from aiohttp.request(
            "POST",
            "http://{host}:{port}/{path}".format(
                host = self._options["host"], port = self._options["port"], path = path),
            params = params,
            data = data,
            connector = self._connector)
        assert res.status == 200
        body = yield from res.read()
        return body

    @asyncio.coroutine
    def postJson(self, *args, **kwargs):
        content = yield from self.post(*args, **kwargs)
        res = content.decode("utf-8")
        return json.loads(res, cls = UnquotingJsonDecoder)

    @asyncio.coroutine
    def postJson2(self, *args, **kwargs):
        result = yield from self.postJson(*args, **kwargs)
        rtn = result["rtn"]
        if not rtn == 0:
            raise ValueError("rtn is not 0, but {}".format(rtn))
        del result["rtn"]
        return result

    @asyncio.coroutine
    def post_del(self, tasks: "iterable of id", recycle: bool, delete: bool):
        # xware doesn't recognize encoded "," (%2C)
        workaround = "?tasks=" + ",".join(map(str, tasks))
        result = yield from self.postJson2(
            "del" + workaround,
            params = OrderedDict([
                ("v", 2),
                ("recycleTask", int(recycle)),
                ("deleteFile", int(delete)),
                ("callback", ""),
            ]),
        )
        return result

    @asyncio.coroutine
    def post_restore(self, tasks: "iterable of id"):
        # xware doesn't recognize encoded "," (%2C)
        workaround = "?tasks=" + ",".join(map(str, tasks))
        result = yield from self.postJson2(
            "restore" + workaround,
            params = OrderedDict([
                ("v", 2),
                ("callback", ""),
            ])
        )
        return result

    @asyncio.coroutine
    def post_settings(self, settings: dict):
        assert isinstance(settings, dict)
        for key, value in settings.items():
            assert key in Settings._fields

        settings["v"] = 2
        result = yield from self.postJson2(
            "settings",
            params = settings,
        )
        return result

    @asyncio.coroutine
    def post_pause(self, tasks: "iterable of id"):
        # xware doesn't recognize encoded "," (%2C)
        workaround = "?tasks=" + ",".join(map(str, tasks))
        result = yield from self.postJson2(
            "pause" + workaround,
            params = OrderedDict([
                ("v", 2),
                ("callback", ""),
            ]),
        )
        return result

    @asyncio.coroutine
    def post_start(self, tasks: "iterable of id"):
        # xware doesn't recognize encoded "," (%2C)
        workaround = "?tasks=" + ",".join(map(str, tasks))
        result = yield from self.postJson2(
            "start" + workaround,
            params = OrderedDict([
                ("v", 2),
                ("callback", ""),
            ]),
        )
        return result

    @asyncio.coroutine
    def post_openLixianChannel(self, taskId: int, enable: bool):
        result = yield from self.postJson2(
            "openLixianChannel",
            params = OrderedDict([
                ("v", 2),
                ("taskid", taskId),
                ("open", "true" if enable else "false"),
            ]),
        )
        return result

    @asyncio.coroutine
    def post_openVipChannel(self, taskId: int):
        result = yield from self.postJson2(
            "openVipChannel",
            params = OrderedDict([
                ("v", 2),
                ("taskid", taskId),
                ("callback", ""),
            ]),
        )
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
        result = yield from self.postJson2(
            "urlCheck",
            params = OrderedDict([
                ("v", 2),
                ("type", int(UrlCheckType.BitTorrentFile)),
                ("upload", int(True)),
                ("callback", ""),
            ]),
            data = files,
        )

        return result

    @asyncio.coroutine
    def post_createTask(self, path, url, name):
        result = yield from self.postJson2(
            "createOne",
            params = OrderedDict([
                ("v", 2),
                ("type", int(UrlCheckType.Url)),
                ("path", path),
                ("url", url),
                ("name", name),
                ("fixed_id", int(True)),
                ("callback", ""),
            ]),
        )
        return result

    @asyncio.coroutine
    def post_createBtTask(self, path, url, name, sub):
        result = yield from self.postJson2(
            "createOne",
            params = OrderedDict([
                ("v", 2),
                ("type", int(UrlCheckType.BitTorrentFile)),
                ("path", path),
                ("url", url),
                ("name", name),
                ("fixed_id", int(True)),
                ("btSub", sub),
                ("callback", ""),
            ]),
        )
        return result

    @asyncio.coroutine
    def post_unbind(self):
        pass

    @asyncio.coroutine
    def post_bind(self):
        pass
