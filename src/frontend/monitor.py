# -*- coding: utf-8 -*-

from ui_monitor import MonitorWidget, Ui_Form

class MonitorWindow(MonitorWidget, Ui_Form):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setupUi(self)
        self.setStyleSheet("background: skyblue;")
