import QtQuick 2.2
import QtQuick.Controls 1.1

Item {
    Rectangle {
        anchors.fill: parent
        color: "red"

        Column {
            ExclusiveGroup { id: group1 }
            ExclusiveGroup { id: group2 }
            Text {
                text: "在完成"
            }
            RadioButton {
                text: qsTr("所有的任务")
                exclusiveGroup: group1
                checked: true
            }
            RadioButton {
                text: qsTr("选择的任务")
                exclusiveGroup: group1
            }
            Text {
                text: "执行"
            }
            Column {
                RadioButton {
                    text: qsTr("无")
                    exclusiveGroup: group2
                    checked: true
                }
                RadioButton {
                    text: qsTr("关机")
                    exclusiveGroup: group2
                    checked: false
                }
                RadioButton {
                    text: qsTr("混合休眠")
                    exclusiveGroup: group2
                    checked: false
                }
                RadioButton {
                    text: qsTr("休眠")
                    exclusiveGroup: group2
                    checked: false
                }
                RadioButton {
                    text: qsTr("睡眠")
                    exclusiveGroup: group2
                    checked: false
                }
            }
        }
    }
}
