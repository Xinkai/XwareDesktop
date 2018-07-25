#include <QVariantMap>
#include <QMetaType>

struct GroupProperty {
    int itemId;
    QVariantMap property;
};

Q_DECLARE_METATYPE(GroupProperty)

class DBusTypes {
    static int GroupPropertyType;

    public:
        static int registerGroupProperty();
};
