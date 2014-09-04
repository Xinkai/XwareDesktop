# -*- coding: utf-8 -*-

from urllib import parse
from urllib.parse import ParseResult


def getInfoFromED2K(netloc: ParseResult.netloc):
    parts = netloc.split("|")
    assert parts[0] == ""
    assert parts[1] == "file"
    filename = parts[2]
    size = parts[3]
    return parse.unquote(filename), size


def getFilenameFromParsed(parsed: ParseResult):
    path = parsed.path
    filename = parse.unquote(path[path.rindex("/") + 1:])
    if not filename:
        return "未命名"
    return filename
