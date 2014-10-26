# -*- coding: utf-8 -*-

from enum import IntEnum, unique
import logging

from PyQt5.QtCore import QObject, QMetaType, pyqtSlot, pyqtProperty, Q_CLASSINFO, pyqtSignal
from PyQt5.QtDBus import QDBusInterface, QDBusArgument, QDBusAbstractAdaptor, \
    QDBusObjectPath, QDBusMessage
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QSystemTrayIcon, QMenu


@unique
class DBusMenuAction(IntEnum):
    Root = 0
    ToggleMainWindow = 1
    ToggleMonitorWindow = 2
    Settings = 3
    Exit = 4

if not hasattr(QDBusArgument, "Structure"):
    QDBusArgument.Structure = 3


def newDBusMenuItem(action: DBusMenuAction, properties, children):
    item = QDBusArgument()
    item.beginStructure()
    item.add(action.value, QMetaType.Int)  # id
    item.add(properties, QMetaType.QVariantMap)
    item.add(children, QMetaType.QVariantList)
    item.endStructure()
    return item


class KdeStatusNotifierAdapter(QDBusAbstractAdaptor):
    # The Ubuntu implementation requires Menu, Id, Category, Status, IconName
    Q_CLASSINFO("D-Bus Interface", "org.kde.StatusNotifierItem")
    Q_CLASSINFO("D-Bus Introspection", """
<interface name="org.kde.StatusNotifierItem">
    <property access="read" type="s" name="Category"/>
    <property access="read" type="s" name="Id"/>
    <property access="read" type="s" name="Title"/>
    <property access="read" type="s" name="Status"/>
    <property access="read" type="i" name="WindowId"/>
    <!-- An additional path to add to the theme search path to find the icons specified above. -->
    <property access="read" type="s" name="IconThemePath"/>
    <property access="read" type="o" name="Menu"/>
    <property access="read" type="b" name="ItemIsMenu"/>
    <!-- main icon -->
    <!-- names are preferred over pixmaps -->
    <property access="read" type="s" name="IconName"/>
    <!--struct containing width, height and image data-->
    <property access="read" type="(iiay)" name="IconPixmap">
        <annotation value="KDbusImageVector" name="com.trolltech.QtDBus.QtTypeName"/>
    </property>
    <property access="read" type="s" name="OverlayIconName"/>
    <property access="read" type="(iiay)" name="OverlayIconPixmap">
        <annotation value="KDbusImageVector" name="com.trolltech.QtDBus.QtTypeName"/>
    </property>
    <!-- Requesting attention icon -->
    <property access="read" type="s" name="AttentionIconName"/>
    <!--same definition as image-->
    <property access="read" type="(iiay)" name="AttentionIconPixmap">
        <annotation value="KDbusImageVector" name="com.trolltech.QtDBus.QtTypeName"/>
    </property>
    <property access="read" type="s" name="AttentionMovieName"/>
    <!-- tooltip data -->
    <!--(iiay) is an image-->
    <property access="read" type="(s(iiay)ss)" name="ToolTip">
        <annotation value="KDbusToolTipStruct" name="com.trolltech.QtDBus.QtTypeName"/>
    </property>
    <!-- interaction: the systemtray wants the application to do something -->
    <method name="ContextMenu">
        <!-- we're passing the coordinates of the icon,
            so the app knows where to put the popup window -->
        <arg direction="in" type="i" name="x"/>
        <arg direction="in" type="i" name="y"/>
    </method>
    <method name="Activate">
        <arg direction="in" type="i" name="x"/>
        <arg direction="in" type="i" name="y"/>
    </method>
    <method name="SecondaryActivate">
        <arg direction="in" type="i" name="x"/>
        <arg direction="in" type="i" name="y"/>
    </method>
    <method name="Scroll">
        <arg direction="in" type="i" name="delta"/>
        <arg direction="in" type="s" name="orientation"/>
    </method>
    <!-- Signals: the client wants to change something in the status-->
    <signal name="NewTitle"/>
    <signal name="NewIcon"/>
    <signal name="NewIconTheme">
        <arg type="s" name="status"/>
    </signal>
    <signal name="NewAttentionIcon"/>
    <signal name="NewOverlayIcon"/>
    <signal name="NewToolTip"/>
    <signal name="NewStatus">
        <arg type="s" name="status"/>
    </signal>
</interface>
    """)

    def __init__(self, parent = None):
        super().__init__(parent)
        self._iconName = ""

    # methods
    @pyqtSlot(int, int)
    def Activate(self, x: int, y: int):
        # Left-click
        pass

    @pyqtSlot(int, int)
    def ContextMenu(self, x: int, y: int):
        raise RuntimeError("What the fuck, it worked!")

    @pyqtSlot(int, str)
    def Scroll(self, delta: int, orientation: str):
        pass

    @pyqtSlot(int, int)
    def SecondaryActivate(self, x: int, y: int):
        # Middle-click
        pass

    # properties
    @pyqtProperty(bool)
    def ItemIsMenu(self):
        return False

    @pyqtProperty(int)
    def WindowId(self):
        return 0

    @pyqtProperty(QDBusObjectPath)
    def Menu(self):
        return QDBusObjectPath("/MenuBar")

    @pyqtProperty(str)
    def AttentionIconName(self):
        return ""

    @pyqtProperty(str)
    def AttentionMovieName(self):
        return ""

    @pyqtProperty(str)
    def Category(self):
        return "ApplicationStatus"

    @pyqtProperty(str)
    def IconName(self):
        return self._iconName

    def setIconName(self, value):
        self._iconName = value
        self.NewIcon.emit()

    @pyqtProperty(str)
    def IconThemePath(self):
        return ""

    @pyqtProperty(str)
    def Id(self):
        return "XwareDesktop"

    @pyqtProperty(str)
    def OverlayIconName(self):
        return ""

    @pyqtProperty(str)
    def Status(self):
        return "Active"

    @pyqtProperty(str)
    def Title(self):
        return "Xware Desktop"

    # signals
    NewAttentionIcon = pyqtSignal()
    NewIcon = pyqtSignal()
    NewIconThemePath = pyqtSignal(str)
    NewTitle = pyqtSignal()
    NewStatus = pyqtSignal(str)
    NewOverlayIcon = pyqtSignal()
    NewToolTip = pyqtSignal()


class CanonicalDBusMenuAdapter(QDBusAbstractAdaptor):
    # http://bazaar.launchpad.net/~dbusmenu-team/libdbusmenu/trunk.14.10/view/head:/
    # libdbusmenu-glib/dbus-menu.xml
    Q_CLASSINFO("D-Bus Interface", "com.canonical.dbusmenu")
    Q_CLASSINFO("D-Bus Introspection", """
<interface name="com.canonical.dbusmenu">
    <method name="GetLayout">
        <arg type="i" name="parentId" direction="in"></arg>
        <arg type="i" name="recursionDepth" direction="in"></arg>
        <arg type="as" name="propertyNames" direction="in"></arg>
        <arg type="u" name="revision" direction="out"></arg>
        <arg type="(ia{sv}av)" name="layout" direction="out"></arg>
    </method>
    <method name="GetGroupProperties">
        <arg type="ai" name="ids" direction="in"></arg>
        <arg type="as" name="propertyNames" direction="in"></arg>
        <arg type="a(ia{sv})" name="properties" direction="out"></arg>
    </method>
    <method name="GetProperty">
        <arg type="i" name="id" direction="in"></arg>
        <arg type="s" name="name" direction="in"></arg>
        <arg type="v" name="value" direction="out"></arg>
    </method>
    <method name="Event">
        <arg type="i" name="id" direction="in"></arg>
        <arg type="s" name="eventId" direction="in"></arg>
        <arg type="v" name="data" direction="in"></arg>
        <arg type="u" name="timestamp" direction="in"></arg>
    </method>
    <method name="EventGroup">
        <arg type="a(isvu)" name="events" direction="in"></arg>
        <arg type="ai" name="idErrors" direction="out"></arg>
    </method>
    <method name="AboutToShow">
        <arg type="i" name="id" direction="in"></arg>
        <arg type="b" name="needUpdate" direction="out"></arg>
    </method>
    <method name="AboutToShowGroup">
        <arg type="ai" name="ids" direction="in"></arg>
        <arg type="ai" name="updatesNeeded" direction="out"></arg>
        <arg type="ai" name="idErrors" direction="out"></arg>
    </method>

    <signal name="ItemsPropertiesUpdated">
        <arg type="a(ia{sv})" name="updatedProps"></arg>
        <arg type="a(ias)" name="removedProps"></arg>
    </signal>
    <signal name="LayoutUpdated">
        <arg type="u" name="revision"></arg>
        <arg type="i" name="parent"></arg>
    </signal>
    <signal name="ItemActivationRequested">
        <arg type="i" name="id"></arg>
        <arg type="u" name="timestamp"></arg>
    </signal>

    <property type="u" name="Version" access="read"></property>
    <property type="s" name="TextDirection" access="read"></property>
    <property type="s" name="Status" access="read"></property>
    <property type="as" name="IconThemePath" access="read"></property>
</interface>
    """)

    def __init__(self, *, sessionService, settings, app, parent):
        super().__init__(parent)
        self.__sessionService = sessionService
        self.__settings = settings
        self.__app = app
        self._revision = 0
        self.__app.applySettings.connect(self.updateLayout)

    def updateLayout(self):
        self._revision += 1
        msg = QDBusMessage.createSignal("/MenuBar", "com.canonical.dbusmenu", "LayoutUpdated")
        msg.setArguments([
            QDBusArgument(self._revision, QMetaType.UInt),
            QDBusArgument(DBusMenuAction.Root.value, QMetaType.Int),
        ])
        self.__sessionService.sessionBus.send(msg)

    # methods
    @pyqtSlot(QDBusMessage)
    def AboutToShow(self, msg) -> "needUpdate(bool)":
        reply = msg.createReply([False])
        return self.__sessionService.sessionBus.send(reply)

    @pyqtSlot(QDBusMessage)
    def AboutToShowGroup(self, msg):
        reply = msg.createReply([
            [0], []
        ])
        return self.__sessionService.sessionBus.send(reply)

    @pyqtSlot(QDBusMessage)
    def Event(self, msg):
        itemId, eventId, data, timestamp = msg.arguments()
        if eventId in ("opened", "closed"):
            # Should be handled at the other end of the D-Bus, don't care.
            return

        if itemId == DBusMenuAction.Root:
            # Has nothing to do
            return

        if itemId == DBusMenuAction.ToggleMonitorWindow and eventId == "clicked":
            show = self.__settings.getbool("frontend", "showmonitorwindow")
            self.__settings.setbool("frontend", "showmonitorwindow", not show)
            self.__app.applySettings.emit()

        if itemId == DBusMenuAction.Exit and eventId == "clicked":
            self.__app.quit()

    @pyqtSlot(QDBusMessage)
    def EventGroup(self, msg):
        print("EventGroup", msg.arguments())

    @pyqtSlot(QDBusMessage)
    def GetGroupProperties(self, msg):
        print("GetGroupProperties", msg.arguments())

    @pyqtSlot(QDBusMessage)
    def GetLayout(self, msg):
        parentId, recursionDepth, propertyNames = msg.arguments()
        if parentId != 0:
            raise NotImplementedError("Don't know when happens when parentId is not 0.")

        exitItem = newDBusMenuItem(DBusMenuAction.Exit, {
            "label": "退出",
            "icon-name": "application-exit",
        }, [])

        # toggleMainWinItem = newDBusMenuItem(DBusMenuAction.ToggleMainWindow, {
        #     "label": "显示主窗口",
        #     "toggle-type": "checkmark",
        #     "toggle-state": 0,
        # }, [])

        # settingsItem = newDBusMenuItem(DBusMenuAction.Settings, {
        #     "label": "设置",
        # }, [])

        toggleMonitorWinItem = newDBusMenuItem(DBusMenuAction.ToggleMonitorWindow, {
            "label": "显示悬浮窗",
            "toggle-type": "checkmark",
            "toggle-state": int(self.__settings.getbool("frontend", "showmonitorwindow")),
        }, [])

        rootItem = newDBusMenuItem(DBusMenuAction.Root, {
            "children-display": "submenu",
        }, [
            toggleMonitorWinItem,
            exitItem,
        ])

        reply = msg.createReply([
            QDBusArgument(self._revision, QMetaType.UInt),
            QDBusArgument(rootItem, QDBusArgument.Structure),
        ])
        return self.__sessionService.sessionBus.send(reply)

    @pyqtSlot(QDBusMessage)
    def GetProperties(self, msg):
        print("GetProperties", msg.arguments())

    # properties
    @pyqtProperty("QStringList")
    def IconThemePath(self):
        return []

    @pyqtProperty(str)
    def Status(self):
        return "normal"

    @pyqtProperty(str)
    def TextDirection(self):
        return "ltr"

    @pyqtProperty("uint")
    def Version(self):
        return 3

    # signals
    ItemActivationRequested = pyqtSignal(int, "uint")
    ItemsPropertiesUpdated = pyqtSignal()  # complex
    LayoutUpdated = pyqtSignal("uint", int)


class KdeSystemTrayIcon(QObject):
    activated = pyqtSignal(QSystemTrayIcon.ActivationReason)

    def __init__(self, application):
        super().__init__(application)
        self.__sessionService = application.sessionService
        self.__settings = application.settings

        self._menubarAdapter = CanonicalDBusMenuAdapter(
            sessionService = self.__sessionService,
            settings = self.__settings,
            app = application,
            parent = self,
        )
        self.__sessionService.registerObject(
            "/MenuBar", self._menubarAdapter,
        )

        self._sniAdapter = KdeStatusNotifierAdapter(self)
        self.__sessionService.registerObject(
            "/StatusNotifierItem", self._sniAdapter,
        )

        self._interface = QDBusInterface(
            "org.kde.StatusNotifierWatcher",
            "/StatusNotifierWatcher",
            "org.kde.StatusNotifierWatcher",
        )

    # Implement necessary interface to mimic QSystemTrayIcon
    def setIcon(self, qIcon: QIcon):
        # extract QIcon's name
        iconName = qIcon.name()
        if not iconName:
            raise ValueError("only support theme icon.")
        self._sniAdapter.setIconName(iconName)

    def setContextMenu(self, qMenu: QMenu):
        pass

    def setVisible(self, visible: bool):
        if visible:
            self._interface.call(
                "RegisterStatusNotifierItem",
                QDBusArgument(self.__sessionService.serviceName, QMetaType.QString),
            )
        else:
            # Maybe try unregistering the whole object?
            raise NotImplementedError("UnregisterStatusNotifierItem method doesn't exist.")
