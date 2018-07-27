# -*- coding: utf-8 -*-

import os

if os.name == "posix":
    from ._DBusSessionService import DBusService as SessionService
elif os.name == "nt":
    from ._NtSessionService import NtService as SessionService
else:
    SessionService = None
