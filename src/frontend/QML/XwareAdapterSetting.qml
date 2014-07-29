import QtQuick 2.2
import QtQuick.Controls 1.1

Rectangle {
    anchors.fill: parent

    Column {
        CheckBox {
            id: useLocalXwared
            text: "本地xwared管理"
            enabled: false
            checked: true
        }

        ListView {
            id: mount
            visible: useLocalXwared.checked
        }

        TextField {
            id: ipHostAddress
            text: "127.0.0.1:9000"
            enabled: !useLocalXwared
            visible: !useLocalXwared
        }
    }


}
