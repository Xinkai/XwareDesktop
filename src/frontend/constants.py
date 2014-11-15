# -*- coding: utf-8 -*-

import sys
from shared.constants import *


# ## Frontend
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
FRONTEND_LOCK = os.path.join(TMP_DIR, "xware_frontend.lock")
FRONTEND_CONFIG_FILE = os.path.join(PROFILE_DIR, "etc/frontend.ini")
if sys.platform == "linux":
    FRONTEND_SOCKET = (os.path.join(TMP_DIR, "xware_frontend.socket"), "AF_UNIX")
elif sys.platform == "win32":
    from utils.system import getCurrentSessionId
    FRONTEND_SOCKET = (r"\\.\pipe\Xware_Desktop_" + str(getCurrentSessionId()), "AF_PIPE")
else:
    raise NotImplementedError()


# ## Legacy
LOGIN_PAGE = "http://yuancheng.xunlei.com/login.html"
V2_PAGE = "http://yuancheng.xunlei.com/"
V3_PAGE = "http://yuancheng.xunlei.com/3/"

XWAREJS_FILE = os.path.join(FRONTEND_DIR, "legacy/xwarejs.js")
XWAREJS_LOGIN_FILE = os.path.join(FRONTEND_DIR, "legacy/loginjs.js")
XWARESTYLE_FILE = os.path.join(FRONTEND_DIR, "legacy/style.css")


# ## Daemon
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


# ## Autostart
DESKTOP_FILE = "/usr/share/applications/xware-desktop.desktop"
DESKTOP_AUTOSTART_FILE = os.path.join(XDG_CONFIG_HOME, "autostart/xware-desktop.desktop")

# Session services
DBUS_SESSION_SERVICE = "net.cuoan.XwareDesktop"
