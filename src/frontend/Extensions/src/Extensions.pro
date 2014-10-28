TEMPLATE = lib

CONFIG   += qt warn_on release
QT       += dbus
QT       -= gui

HEADERS  = \
    DBusTypes.hpp
SOURCES  = \
    DBusTypes.cpp
TARGET   = DBusTypes

DESTDIR  = ./build
