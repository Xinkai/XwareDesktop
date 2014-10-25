# -*- coding: utf-8 -*-

import os

from PyQt5.QtCore import QCoreApplication


CompatSystemTrayIcon = None
if os.name == "posix":
    app = QCoreApplication.instance()
    if app.sessionService.serviceExists("org.kde.StatusNotifierWatcher"):
        from ._KdeSystemTrayIcon import KdeSystemTrayIcon as CompatSystemTrayIcon

if not CompatSystemTrayIcon:
    from PyQt5.QtWidgets import QSystemTrayIcon
    if QSystemTrayIcon.isSystemTrayAvailable():
        CompatSystemTrayIcon = QSystemTrayIcon
    else:
        from ._DummySystemTrayIcon import DummySystemTrayIcon as CompatSystemTrayIcon
