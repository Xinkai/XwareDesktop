TEMPLATE = lib

CONFIG   += qt warn_on release c++11
QT       += dbus
QT       -= gui

HEADERS  = \
    DBusTypes.hpp
SOURCES  = \
    DBusTypes.cpp
TARGET   = DBusTypes

DESTDIR  = ./build
