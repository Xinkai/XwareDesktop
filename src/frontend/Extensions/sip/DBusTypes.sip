%Module DBusTypes

%Import QtCore/QtCoremod.sip


class DBusTypes {

%TypeHeaderCode
    #include "../src/DBusTypes.hpp"
%End

public:
    static int registerGroupProperty();
};
