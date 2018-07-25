import QtQuick 2.2
import QtQuick.Layouts 1.1

Rectangle {
    Column {
        Repeater {
            model: adapters.itr()
            XwareAdapterSetting {
                adapter: adapters.adapter(modelData)
            }
        }
    }
}
