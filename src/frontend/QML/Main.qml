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
                Layout.minimumWidth: parent.width * 0.618
                Layout.maximumWidth: parent.width * 0.75
                height: parent.height
                model: taskModel
                headerVisible: false
                selectionMode: SelectionMode.ExtendedSelection

                TableViewColumn {
                    role: "taskData"
                    delegate: TaskDelegate {}
                }

                rowDelegate: Item {
                    height: 60
                }

                onActivated: {
                    console.log("TODO")
                }
            }

            Item {
                id: metaSideBar
                Layout.maximumWidth: 0.382 * splitView.width
                Layout.minimumWidth: 0.25 * splitView.width
                height: splitView.height

                Loader {
                    id: metaSideBarLoader
                    visible: status === Loader.Ready
                    source: {
                        if (tableView.currentRow >= 0) return "TaskSidebar.qml"

                        return "AboutSidebar.qml"
                    }

                    property var taskData: null
                    readonly property var buddyView: tableView

                    function setTaskData() {
                        var currentRow = tableView.currentRow
                        if (currentRow >= 0) {
                            metaSideBarLoader.taskData = taskModel.get(currentRow)
                        } else {
                            metaSideBarLoader.taskData = null
                        }
                    }

                    Connections {
                        target: taskModel

                        function handleSrcDataChanged(row1, row2) {
                            var currentRow = tableView.currentRow
                            if ((row1 <= currentRow) && (currentRow <= row2)) {
                                metaSideBarLoader.setTaskData()
                            }
                        }

                        onSrcDataChanged: handleSrcDataChanged(arguments[0], arguments[1])
                    }

                    Connections {
                        target: tableView.selection
                        onSelectionChanged: {
                            metaSideBarLoader.setTaskData()
                        }
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
