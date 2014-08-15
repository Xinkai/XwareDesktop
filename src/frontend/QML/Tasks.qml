import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1

import "JsUtils.js" as JsUtils

import TaskModel 1.0

Item {
    Rectangle {
        id: leftBar
        color: "lightgreen"
        width: 120
        anchors {
            top: parent.top
            bottom: parent.bottom
        }

        Column {
            TaskClassSelector {
                klass: TaskModel.Class_RUNNING
            }

            TaskClassSelector {
                klass: TaskModel.Class_COMPLETED
            }

            TaskClassSelector {
                klass: TaskModel.Class_RECYCLED
            }

            TaskClassSelector {
                klass: TaskModel.Class_FAILED
            }
        }
    }

    Rectangle {
        id: mainArea

        anchors {
            left: leftBar.right
            top: parent.top
            bottom: parent.bottom
            right: parent.right
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
                        ""
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
}
