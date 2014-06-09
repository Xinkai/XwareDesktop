# -*- coding: utf-8 -*-

import os

_DEFAULT_PATTERN = """; 试验功能，暂不允许更改此设置
; packages
*.zip;*.tar;*.tgz;*.tar.gz;*.tbz;*.tbz2;*.tb2;*.tar.bz2;*.taz;*.tar.Z;*.tlz;*.tar.lz;*.tar.lzma;*.txz;*.tar.xz;*.cab;*.rar;*.7z;*.iso;*.dmg;*.img;

; documents
*.pdf;*.doc;*.docx;*.docm;*.xlt;*.xltx;*.xlsm;*.ppt;*.pptx;*.pptm;*.epub;*.chm;*.wps;*.odt;*.rtf;*.txt

; audio
*.mp1;*.mp2;*.mp3;*.mp4;*.flac;*.ape;*.webm;*.ogg;*.wav;*.wv;*.wma;*.aac;*.m4a;*.ra

; video
*.mp4;*.mkv;*.rm;*.rmvb;*.avi;*.flv;*.3gp;*.3g2;*.wmv;*.mov;*.vob

; media-related
*.srt;*.cue;*.m3u;*.sub

; programming
*.jar;*.apk;

; Linux
*.deb;*.rpm

; Windows
*.exe;*.msi;

; Mac

; misc
*.rom;*.ttf;*.bin;*.torrent
"""

DEFAULT_SETTINGS = {
    "account": {
        "username": None,
        "password": None,
        "autologin": True,
    },
    "frontend": {
        "enabledeveloperstools": False,
        "allowflash": True,
        "minimizetosystray": True,
        "closetominimize": False,
        "popnotifications": True,
        "notifybysound": True,
        "cachelocation": os.path.expanduser("~/.xware-desktop/cache/webkit"),
        "showmonitorwindow": True,
        "monitorfullspeed": 512,
        "watchclipboard": True,
        "watchpattern": _DEFAULT_PATTERN,
    },
    "scheduler": {
        "poweroffcmd": "",
        "hybridsleepcmd": "",
        "hibernatecmd": "",
        "suspendcmd": "",
    },
    "internal": {
        "dlspeedlimit": 512,
        "ulspeedlimit": 50,
        "mainwindowgeometry": None,
        "monitorwindowgeometry": None,
    },
}
