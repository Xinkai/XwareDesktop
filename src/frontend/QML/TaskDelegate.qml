import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import "JsUtils.js" as JsUtils

import TaskModel 1.0

Rectangle {
    id: item
    anchors.fill: parent
    readonly property var taskData: styleData.value
    readonly property int stateIconWidth: 40
    readonly property int rightMostWidth: 80
    Rectangle {
        id: progressIndicator
        color: styleData.selected ? "lightsteelblue" : "lightgreen"
        anchors {
            top: parent.top
            bottom: parent.bottom
        }
        width: (taskData.progress / 10000) * item.width
    }

    Row {
        spacing: 0
        anchors.fill: parent

        Rectangle {
            height: parent.height
            width: stateIconWidth
            color: "transparent"
            Image {
                anchors.centerIn: parent.Center
                anchors.fill: parent
                fillMode: Image.Pad
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
        }

        Column {
            spacing: 0
            width: parent.width - stateIconWidth - rightMostWidth
            height: parent.height
            Rectangle {
                width: parent.width
                height: parent.height * .7
                color: "transparent"
                Text {
                    font.family: "Helvetica"
                    font.pointSize: 12
                    elide: Text.ElideRight
                    anchors.fill: parent
                    verticalAlignment: Text.AlignVCenter
                    // FIXME: when flicked, this could generate an error
                    text: taskData.name ? taskData.name : "ERROR"
                }
            }
            Rectangle {
                width: parent.width
                height: parent.height * .3
                color: "transparent"
                Row {
                    Text {
                        color: "grey"
                        text: {
                            if (taskData) {
                                return JsUtils.humanBytes(taskData.size)
                            } else {
                                return ""
                            }
                        }
                    }
                }
            }
        }

        Column {
            spacing: 0
            width: rightMostWidth
            height: parent.height
            Rectangle {
                width: parent.width
                height: parent.height / 2
                color: "transparent"
                Text {
                    font.family: "Comic Sans"
                    anchors.fill: parent
                    horizontalAlignment: Text.AlignRight
                    verticalAlignment: Text.AlignVCenter
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
                width: parent.width
                height: parent.height / 2
                color: "transparent"
                Text {
                    font.family: "Comic Sans"
                    anchors.fill: parent
                    horizontalAlignment: Text.AlignRight
                    verticalAlignment: Text.AlignVCenter
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
}


