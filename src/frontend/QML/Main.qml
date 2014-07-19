import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import "JsUtils.js" as JsUtils

Rectangle {
    Rectangle {
        id: topBar
        color: "orange"
        height: 80
        width: parent.width
        Text {
            text: "TOP BAR"
        }
        TextField {
            text: ""
            anchors.bottom: parent.bottom
            anchors.right: parent.right
            onTextChanged: taskModel.setNameFilter(text)
            placeholderText: "搜索任务名"
        }
    }

    Rectangle {
        id: leftBar
        color: "lightgreen"
        width: 120
        anchors {
            top: topBar.bottom
            bottom: statusBar.top
        }

        Column {
            Rectangle {
                width: leftBar.width
                height: 50
                color: "lightgrey"
                Text {
                    text: "正在下载"
                }
            }

            Rectangle {
                width: leftBar.width
                height: 50
                color: "lightgrey"
                Text {
                    text: "已完成"
                }
            }

            Rectangle {
                width: leftBar.width
                height: 50
                color: "lightgrey"
                Text {
                    text: "垃圾箱"
                }
            }

            Rectangle {
                width: leftBar.width
                height: 50
                color: "lightgrey"
                Text {
                    text: "提交失败"
                }
            }
        }
    }

    Rectangle {
        id: mainArea

        anchors {
            left: leftBar.right
            top: topBar.bottom
            bottom: statusBar.top
            right: topBar.right
        }

        SplitView {
            id: splitView
            anchors.fill: parent
            orientation: Qt.Horizontal

            TableView {
                id: tableView
                width: parent.width * 0.618
                Layout.minimumWidth: parent.width * 0.618
                height: parent.height
                model: taskModel
                headerVisible: false
                selectionMode: SelectionMode.ExtendedSelection

                TableViewColumn {
                    role: "taskData"
                }

                rowDelegate: Item {
                    height: 60
                }

                itemDelegate: TaskDelegate {

                }
            }

            Item {
                id: metaSideBar
                Loader {
                    id: metaSideBarLoader
                    source: {
                        if (tableView.currentRow >= 0) return "TaskSidebar.qml"

                        return "AboutSidebar.qml"
                    }

                    property variant taskData: {
                        tableView.currentRow >= 0 ? taskModel.get(tableView.currentRow): null
                    }

                    readonly property var buddyView: tableView
                    Connections {
                        target: taskModel

                        function handleSrcDataChanged(row1, row2) {
                            console.log(row1, row2, tableView.currentRow)
                            if ((row1 <= tableView.currentRow) && (tableView.currentRow <= row2)) {
                                metaSideBarLoader.taskData = taskModel.get(tableView.currentRow)
                            }
                        }

                        onSrcDataChanged: handleSrcDataChanged(arguments[0], arguments[1])
                    }
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
