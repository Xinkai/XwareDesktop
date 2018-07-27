import QtQuick 2.2
import QtQuick.Controls 1.1

Rectangle {
    property QtObject adapter: null
    anchors.fill: parent

    Column {
        Row {
            Text {
                text: "名称"
            }
            Text {
                text: adapter.name
            }
        }
        Row {
            Text {
                text: "连接"
            }
            Text {
                text: adapter.connection
            }
        }
    }
}
