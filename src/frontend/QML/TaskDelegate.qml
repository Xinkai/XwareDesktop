import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import "JsUtils.js" as JsUtils

import TaskModel 1.0

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
            Image {
                sourceSize.width: 24
                sourceSize.height: 24
                source: {
                    switch (taskData.state) {
                    case TaskModel.State_Downloading:
                        return "image://icon/media-playback-start"
                    case TaskModel.State_Paused:
                        return "image://icon/media-playback-pause"
                    case TaskModel.State_Completed:
                        return "image://icon/media-playback-stop"
                    default:
                        return "image://icon/xware-desktop"
                    }
                }
            }

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
                text: {
                    switch (taskData.state) {
                    case TaskModel.State_Downloading:
                        return JsUtils.humanBytes(taskData.speed) + "/s"
                    default:
                        return ""
                    }
                }
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
                text: {
                    switch (taskData.state) {
                    case TaskModel.State_Downloading:
                        return JsUtils.humanSeconds(taskData.remainingTime)
                    default:
                        return ""
                    }
                }
            }
        }
    }
}


