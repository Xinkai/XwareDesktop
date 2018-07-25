# -*- coding: utf-8 -*-

import sys


if sys.platform == "linux":
    from ._DBusNotifier import Notifier
elif sys.platform == "win32":
    from ._Win32Notifier import Win32Notifier as Notifier
else:
    raise NotImplementedError()
