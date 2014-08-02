# -*- coding: utf-8 -*-

from shared.constants import *

FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

LOGIN_PAGE = "http://yuancheng.xunlei.com/login.html"
V2_PAGE = "http://yuancheng.xunlei.com/"
V3_PAGE = "http://yuancheng.xunlei.com/3/"

XWAREJS_FILE = os.path.join(FRONTEND_DIR, "legacy/xwarejs.js")
XWARESTYLE_FILE = os.path.join(FRONTEND_DIR, "legacy/style.css")

SYSTEMD_SERVICE_FILE = os.path.join(FRONTEND_DIR, "xwared.service")
SYSTEMD_SERVICE_USERFILE = os.path.join(XDG_CONFIG_HOME, "systemd/user/xwared.service")
SYSTEMD_SERVICE_ENABLED_USERFILE = os.path.join(XDG_CONFIG_HOME,
                                                "systemd/user/default.target.wants/xwared.service")

UPSTART_SERVICE_FILE = os.path.join(FRONTEND_DIR, "xwared.conf")
UPSTART_SERVICE_USERFILE = os.path.join(XDG_CONFIG_HOME,
                                        "upstart/xwared.conf")

AUTOSTART_DESKTOP_FILE = os.path.join(FRONTEND_DIR, "xwared.desktop")
AUTOSTART_DESKTOP_USERFILE = os.path.join(XDG_CONFIG_HOME,
                                          "autostart/xwared.desktop")

DESKTOP_FILE = "/usr/share/applications/xware-desktop.desktop"
DESKTOP_AUTOSTART_FILE = os.path.join(XDG_CONFIG_HOME, "autostart/xware-desktop.desktop")
