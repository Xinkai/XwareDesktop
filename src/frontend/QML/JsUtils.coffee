`.pragma library`

"use strict"

humanBytes = (bytes, fragDigits = 2) ->
    kilo = Math.pow(2, 10)
    mega = Math.pow(2, 20)
    giga = Math.pow(2, 30)
    tera = Math.pow(2, 40)

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

humanTimeElapse = (timestamp) ->
    elapse_ms = Date.now() - new Date(timestamp * 1000)
    elapse = (elapse_ms / 1000) | 0  # to seconds

    year = elapse / (60 * 60 * 24 * 365) | 0
    if year
        return "#{year}年前"
    month = elapse / (60 * 60 * 24 * 30) | 0
    if month
        return "#{month}月前"
    day = elapse / (60 * 60 * 24) | 0
    if day
        return "#{day}天前"
    hour = elapse / (60 * 60) | 0
    if hour
        return "#{hour}小时前"
    minute = elapse / 60 | 0
    if minute
        return "#{minute}分钟前"
    return "刚才"
