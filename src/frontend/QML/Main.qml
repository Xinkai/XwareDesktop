import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1
import "JsUtils.js" as JsUtils

import TaskModel 1.0

Rectangle {
    Rectangle {
        id: topBar
        color: "orange"
        height: 10
        width: parent.width
    }

    TabView {
        anchors {
            top: topBar.bottom
            bottom: statusBar.top
            left: parent.left
            right: parent.right
        }

        Tab {
            id: tabMain
            title: "任务"
            source: "Tasks.qml"
        }

        Tab {
            id: tabSetting
            title: "设置"
            source: "Settings.qml"
        }

        Tab {
            id: scheduler
            title: "计划任务"
            source: "Scheduler.qml"
        }

        Tab {
            id: tabFeedback
            title: "反馈"
            source: "Feedback.qml"
        }

        Tab {
            id: tabAbout
            source: "About.qml"
            title: "关于"
        }

        style: TabViewStyle {
            tabBar: Rectangle {
                color: "orange"
                height: 180
                Button {
                    text: "新建任务"
                    anchors.bottom: parent.bottom
                    anchors.right: searchBar.left
                    onClicked: taskCreationAgent.createTasksAction()
                }
                TextField {
                    id: searchBar
                    text: ""
                    anchors.bottom: parent.bottom
                    anchors.right: parent.right
                    onTextChanged: taskModel.setNameFilter(text)
                    placeholderText: "搜索任务名"
                }
            }
            tab: Rectangle {
                color: styleData.selected ? "steelblue" :"lightsteelblue"
                border.color:  "steelblue"
                implicitWidth: 80
                implicitHeight: 28
                Text {
                    id: text
                    anchors.centerIn: parent
                    text: styleData.title
                    color: styleData.selected ? "white" : "black"
                    font.bold: styleData.selected
                }
            }
        }
    }

    StatusBar {
        id: statusBar
        anchors.bottom: parent.bottom
        Text {
            text: "这是一个处于桑葚胚阶段的试验性质的界面。"
        }

        Rectangle {
            anchors.right: parent.right
            width: 220
            RowLayout {
                Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
                Text {
                    text: "上传:" + JsUtils.humanBytes(adapters.ulSpeed) + "/s"
                }
                Text {
                    text: "下载:" + JsUtils.humanBytes(adapters.dlSpeed) + "/s"
                }
            }
        }
    }
}
