#include <QtDBus>
#include <QDebug>
#include <QDBusMetaType>
#include "DBusTypes.hpp"

// initialize everything to Unknown
int DBusTypes::GroupPropertyType = QMetaType::UnknownType;

int DBusTypes::registerGroupProperty() {
    if (GroupPropertyType == QMetaType::UnknownType) {
        GroupPropertyType = qDBusRegisterMetaType<GroupProperty>();
    } else {
        qDebug() << "GroupProperty already registered with id: " << GroupPropertyType;
    }
    return GroupPropertyType;
}

inline QDBusArgument &operator<<(QDBusArgument &argument, const GroupProperty &groupProperty) {
    argument.beginStructure();
    argument << groupProperty.itemId << groupProperty.property;
    argument.endStructure();
    return argument;
}

inline const QDBusArgument &operator>>(const QDBusArgument &argument, GroupProperty &groupProperty) {
    argument.beginStructure();
    argument >> groupProperty.itemId >> groupProperty.property;
    argument.endStructure();
    return argument;
}
