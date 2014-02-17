# -*- coding: utf-8 -*-

def getHumanBytesNumber(byteNum):
    kilo = 1024
    mega = kilo * kilo

    if byteNum >= kilo * kilo:
        return "{:.2f}MB".format(byteNum / mega)
    else:
        return "{:.2f}KB".format(byteNum / kilo)

