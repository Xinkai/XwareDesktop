# -*- coding: utf-8 -*-

import os

_DEFAULT_PATTERN = """// packages
*.zip;*.tar;*.tgz;*.tar.gz;*.tbz;*.tbz2;*.tb2;*.tar.bz2;*.taz;*.tar.Z;*.tlz;*.tar.lz;*.tar.lzma;*.txz;*.tar.xz;*.cab;*.rar;*.7z;*.iso;*.dmg;*.img;

// documents
*.pdf;*.doc;*.docx;*.docm;*.xlt;*.xltx;*.xlsm;*.ppt;*.pptx;*.pptm;*.epub;*.chm;*.wps;*.odt;*.rtf;*.txt

// audio
*.mp1;*.mp2;*.mp3;*.mp4;*.flac;*.ape;*.webm;*.ogg;*.wav;*.wv;*.wma;*.aac;*.m4a;*.ra

// video
*.mp4;*.mkv;*.rm;*.rmvb;*.avi;*.flv;*.3gp;*.3g2;*.wmv;*.mov;*.vob

// media-related
*.srt;*.cue;*.m3u;*.sub

// programming
*.jar;*.apk;

// Linux
*.deb;*.rpm

// Windows
*.exe;*.msi;

// Mac

// misc
*.rom;*.ttf;*.bin;*.torrent
"""

DEFAULT_SETTINGS = {
    "frontend": {
        "minimizetosystray": True,
        "closetominimize": False,
        "popnotifications": True,
        "notifybysound": True,
        "showmonitorwindow": True,
        "monitorfullspeed": 512,
        "watchclipboard": True,
        "watchpattern": _DEFAULT_PATTERN,
    },
    "legacy": {
        "autologin": True,
        "allowflash": True,
        "cachelocation": os.path.expanduser("~/.xware-desktop/cache/webkit"),
        "enabledeveloperstools": False,
        "webviewminsizeoverride": None,
        "webviewzoom": None,
    },
    "adapter-legacy": {
        "type": "xware",
        "connection": "~/.xware-desktop/profile/tmp/xware_xwared.socket",
        "name": "本机xwared",
        "dlspeedlimit": 512,
        "ulspeedlimit": 50,
        "username": None,
        "password": None,
    },
    "scheduler": {
        "poweroffcmd": "",
        "hybridsleepcmd": "",
        "hibernatecmd": "",
        "suspendcmd": "",
    },
    "internal": {
        "mainwindowgeometry": None,
        "monitorwindowgeometry": None,
        "previousversion": "0.8",
        "previousdate": 0,
    },
}
