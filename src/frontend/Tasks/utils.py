# -*- coding: utf-8 -*-

from collections import namedtuple
from urllib import parse
from urllib.parse import ParseResult

from .bencode import bdecode, BTFailure

FileResolution = namedtuple("FileResolution", ["name", "size"])


def resolveEd2k(parsed: ParseResult):
    parts = parsed.netloc.split("|")
    assert parts[0] == ""
    assert parts[1] == "file"
    filename = parts[2]
    size = parts[3]
    return [FileResolution(parse.unquote(filename), size)]


def resolveNormal(parsed: ParseResult):
    path = parsed.path
    filename = parse.unquote(path[path.rindex("/") + 1:])
    if not filename:
        return "未命名"
    return [FileResolution(filename, 0)]


def resolveTorrentFile(contents: bytes) -> False or FileResolution:
    assert isinstance(contents, bytes)

    try:
        result = bdecode(contents)
    except BTFailure:
        return False

    try:
        encoding = result[b"encoding"].decode("ascii")
    except KeyError:
        encoding = "utf-8"
    info = result[b"info"]

    if b"files" in info:
        # multiple files
        dirName = info[b"name"].decode(encoding)
        fileRes = [
            FileResolution(
                name = "%s/%s" % (dirName, file[b"path"][0].decode(encoding)),
                size = file[b"length"]
            )
            for file in info[b"files"]
        ]
    else:
        # single file
        fileRes = [
            FileResolution(
                name = info[b"name"].decode(encoding),
                size = info[b"length"]
            )
        ]

    return fileRes


def resolveMagnet(parsed: ParseResult) -> FileResolution:
    queryParts = parsed.query.split("&")
    query = dict()
    for part in queryParts:
        key, value = part.split("=")
        query[key] = value

    if "dn" in query:
        return [FileResolution(parse.unquote_plus(query["dn"]), 0)]
    else:
        return [FileResolution("<磁力链接任务>", 0)]
