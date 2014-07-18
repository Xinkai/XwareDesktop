`.pragma library`

"use strict"

humanBytes = (bytes, fragDigits = 2) ->
    kilo = 2 ** 10
    mega = 2 ** 20
    giga = 2 ** 30
    tera = 2 ** 40

    if bytes >= tera
        (bytes / tera).toFixed(fragDigits) + "TiB"
    else if bytes >= giga
        (bytes / giga).toFixed(fragDigits) + "GiB"
    else if bytes >= mega
        (bytes / mega).toFixed(fragDigits) + "MiB"
    else
        (bytes / kilo).toFixed(fragDigits) + "KiB"

padLeft = (src, padder, len) ->
    src = src + ""
    if src.length <= len
        return (new Array(len - src.length + 1)).join(padder) + src
    else
        return src

humanSeconds = (seconds) ->
    hour = (seconds / 3600) | 0
    minute = ((seconds / 60) % 60) | 0
    second = seconds % 60 | 0
    "#{padLeft(hour, '0', 2)}:#{padLeft(minute, '0', 2)}:#{padLeft(second, '0', 2)}"

humanDatetime = (timestamp) ->
    new Date(timestamp * 1000).toString()
