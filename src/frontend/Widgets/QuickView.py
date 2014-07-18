# -*- coding: utf-8 -*-

from PyQt5.QtQuick import QQuickView


class QmlError(Exception):
    def __init__(self, errors: "list<QQmlError>"):
        output = "".join(map(lambda generator: self.formatOneError(*generator),
                             enumerate(errors)))
        super().__init__(output)

    @staticmethod
    def formatOneError(i: "Error Sequence", error):
        output = """\n\tError({i}) {url}, line {line}
\t\t{description}
""".format(i = i, url = error.url().url(), line = error.line(), column = error.column(),
           description = error.description())
        return output


class StrictQmlError(QmlError):
    """Non-fatal Qml Error, raise them anyway."""


class QmlLoadingError(QmlError):
    """Qml cannot be loaded."""


class CustomQuickView(QQuickView):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.engine().warnings.connect(self.strictWarn)
        self.engine().setOutputWarningsToStandardError(False)  # let .strictWarn handle it!

        self.statusChanged.connect(self.slotStatusChanged)

    def strictWarn(self, errors):
        raise StrictQmlError(errors)

    def slotStatusChanged(self, status: "QQuickView::Status"):
        if status == QQuickView.Error:
            raise QmlLoadingError(self.errors())


from PyQt5.QtQml import QQmlEngine


class QuickApplicationWindow(object):
    def __init__(self):
        self.engine = QQmlEngine()
