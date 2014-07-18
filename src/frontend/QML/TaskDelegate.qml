import QtQuick 2.2
import QtQuick.Controls 1.2
import QtQuick.Layouts 1.1
import "JsUtils.js" as JsUtils


Rectangle {
    id: item
    anchors.fill: parent
    readonly property var taskData: styleData.value
    property int rightWidth: 75
    property int leftWidth: item.width - rightWidth

    Rectangle {
        id: progressIndicator
        color: styleData.selected ? "lightsteelblue" : "lightgreen"
        anchors {
            top: parent.top
            bottom: parent.bottom
        }
        width: (taskData.progress / 10000) * item.width
    }

    Grid {
        anchors.fill: parent
        columns: 2
        horizontalItemAlignment: Qt.AlignLeft
        verticalItemAlignment: Qt.AlignVCenter
        rowSpacing: 3

        Rectangle {
            width: leftWidth
            height: 30
            color: "transparent"
            Text {
                // FIXME: when flicked, this could generate an error
                text: taskData.name ? taskData.name : "ERROR"
            }
        }
        Rectangle {
            width: rightWidth
            height: 30
            color: "transparent"
            Text {
                horizontalAlignment: Text.AlignRight
                text: JsUtils.humanBytes(taskData.speed) + "/s"
            }
        }
        Rectangle {
            width: leftWidth
            height: 20
            color: "transparent"
            Text {
                text: ""
            }
        }
        Rectangle {
            width: rightWidth
            height: 20
            color: "transparent"
            Text {
                color: "black"
                text: JsUtils.humanSeconds(taskData.remainTime)
            }
        }
    }
}


