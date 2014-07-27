import QtQuick 2.2

import TaskModel 1.0

Rectangle {
    property int klass: null
    width: leftBar.width
    height: 50
    readonly property bool highlighted: taskModel.taskClassFilter & klass
    color: highlighted ? "red" : "lightgrey"
    Text {
        text: {
            switch (klass) {
            case TaskModel.RUNNING:
                return "正在下载"
            case TaskModel.COMPLETED:
                return "已完成"
            case TaskModel.RECYCLED:
                return "垃圾箱"
            case TaskModel.FAILED:
                return "失败的"
            default:
                return "未知的"
            }
        }
    }
    MouseArea {
        anchors.fill: parent
        onClicked: {
            taskModel.taskClassFilter = klass
        }
    }
}
