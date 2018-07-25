# -*- coding: utf-8 -*-

# A workaround for QIcon.fromTheme problems.
# See #161


class ThemeIcon(object):
    def __init__(self, *args, **kwargs):
        self._iconName = None

    @staticmethod
    def fromTheme(name: str):
        result = ThemeIcon()
        result._iconName = name
        return result

    def name(self) -> str:
        return self._iconName
