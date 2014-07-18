import QtQuick 2.2
import QtQuick.Layouts 1.1
import QtQuick.Controls 1.2
import "JsUtils.js" as JsUtils

Rectangle {
    id: item
    Layout.maximumWidth: 0.382 * parent.width
    width: 0.382 * parent.width
    height: parent.height

    ColumnLayout {
        Text {
            text: {
                var selectionCount = buddyView.selection.count
                if (selectionCount === 1) {
                    taskData.name
                } else if (selectionCount > 1) {
                    [taskData.name, "等", selectionCount, "项内容"].join("")
                } else {
                    "无文件选中"
                }
            }
        }
//        SidebarSection {
//            title: "操作"

//        }

        Text {
            text: {
                if (taskData && taskData.speed) {
                    JsUtils.humanBytes(taskData.speed) + "/s"
                } else {
                    "NOSPEED"
                }
            }
        }

        Button {
            text: "打开文件"
            visible: buddyView.selection.count === 1
            onClicked: taskModel.systemOpen(buddyView.currentRow)
        }

        Button {
            text: "在文件夹中查看"
            visible: buddyView.selection.count === 1
            onClicked: taskModel.viewOneTask(buddyView.currentRow)
        }

        Button {
            text: ["在文件夹中查看", buddyView.selection.count, "项内容"].join(" ")
            visible: buddyView.selection.count > 1
            onClicked: {
                var rows = []
                buddyView.selection.forEach(function(row) {
                    rows.push(row)
                })

                taskModel.viewMultipleTasks(rows)
            }
        }

        Button {
            text: "暂停"
            visible: buddyView.selection.count === 1
            onClicked: {
                var rows = []
                buddyView.selection.forEach(function(row) {
                    rows.push(row)
                })

                taskModel.pauseTasks({
                    rows: rows
                })
            }
        }

        Button {
            text: "开始"
            visible: buddyView.selection.count === 1
            onClicked: {
                var rows = []
                buddyView.selection.forEach(function(row) {
                    rows.push(row)
                })

                taskModel.startTasks({
                    rows: rows
                })
            }
        }

        Button {
            text: "离线加速"
            onClicked: {
                taskModel.openLixianChannel(buddyView.currentRow, true)
            }
        }

        Text {
            text: {
                if (taskData && taskData.lixianChannel) {
                    var state = taskData.lixianChannel.state
                    switch (state) {
                    case 0:
                        return "未开启"
                    case 1:
                        return "提交中"
                    case 2:
                        return "云端下载中 " + JsUtils.humanBytes(taskData.lixianChannel.serverSpeed) + "/s"
                    case 3:
                        return "已开启 " + JsUtils.humanBytes(taskData.lixianChannel.speed) + "/s"
                    case 4:
                        return "失败"
                    case 5:
                        return "未知"
                    }
                } else {
                    "不可用2"
                }
            }
        }

        Button {
            text: "高速通道"
            onClicked: {
                taskModel.openVipChannel(buddyView.currentRow, true)
            }
        }

        Text {
            text: {
                if (taskData && taskData.vipChannel) {
                    if (!taskData.vipChannel.available) {
                        return "不可用"
                    }
                    var state = taskData.vipChannel.opened
                    switch (state) {
                    case 0:
                        return "未开启"
                    case 1:
                        return "提交中"
                    case 2:
                        return "已开启 " + JsUtils.humanBytes(taskData.vipChannel.speed)
                    case 3:
                        return "失败"
                    default:
                        return "未知"
                    }
                } else {
                    "不可用2"
                }
            }
        }

        Text {
            text: {
                if (taskData && taskData.createTime) {
                    return JsUtils.humanDatetime(taskData.createTime)
                } else {
                    "NO CREATETIME"
                }
            }
        }

        Text {
            text: taskData && taskData.completeTime ? JsUtils.humanDatetime(taskData.completeTime) : "NO COMPLETETIME"
        }
    }
}
