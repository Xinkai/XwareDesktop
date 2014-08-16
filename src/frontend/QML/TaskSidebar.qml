import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import "JsUtils.js" as JsUtils

import TaskModel 1.0

Rectangle {
    id: item
    ColumnLayout {
        Text {
            text: {
                var selectionCount = buddyView.selection.count
                if ((!taskData) || (selectionCount === 0)) {
                    return "无文件选中"
                }

                if (selectionCount === 1) {
                    taskData.name
                } else if (selectionCount > 1) {
                    [taskData.name, "等", selectionCount, "项内容"].join("")
                }
            }
        }
//        SidebarSection {
//            title: "操作"

//        }

        Text {
            text: {
                if (taskData) {
                    switch (taskData.state) {
                    case TaskModel.State_Downloading:
                        return "下载中"
                    case TaskModel.State_Waiting:
                        return "队列中"
                    case TaskModel.State_Paused:
                        return "已暂停"
                    case TaskModel.State_Completed:
                        return "已完成"
                    case TaskModel.State_Removed:
                        return "已删除"
                    case TaskModel.State_Failed:
                        return "发生错误"
                    case TaskModel.State_Unrecognized:
                        return "未知状态"
                    }
                } else {
                    return "未知状态2"
                }
            }
        }

        Text {
            text: {
                if (taskData && taskData.speed) {
                    JsUtils.humanBytes(taskData.speed) + "/s"
                } else {
                    JsUtils.humanBytes(0) + "/s"
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
            visible: (buddyView.selection.count === 1) &&
                     (taskData) &&
                     (taskData.state === TaskModel.State_Downloading)
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
            visible: (buddyView.selection.count === 1) &&
                     (taskData) &&
                     (taskData.state === TaskModel.State_Paused)
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
                    case TaskModel.Lixian_NOTUSED:
                        return "未开启"
                    case TaskModel.Lixian_SUBMITTING:
                        return "提交中"
                    case TaskModel.Lixian_DOWNLOADING:
                        return "云端下载中 " + JsUtils.humanBytes(taskData.lixianChannel.serverSpeed) + "/s"
                    case TaskModel.Lixian_ACTIVATED:
                        return "已开启 " + JsUtils.humanBytes(taskData.lixianChannel.speed) + "/s"
                    case TaskModel.Lixian_FAILED:
                        return "失败"
                    default:
                        return "未知"
                    }
                } else {
                    "此下载核心不可用"
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
                    var state = taskData.vipChannel.state
                    switch (state) {
                    case TaskModel.Vip_NOTUSED:
                        return "未开启"
                    case TaskModel.Vip_SUBMITTING:
                        return "提交中"
                    case TaskModel.Vip_ACTIVATED:
                        return "已开启 " + JsUtils.humanBytes(taskData.vipChannel.speed)
                    case TaskModel.Vip_FAILED:
                        return "失败"
                    default:
                        return "未知"
                    }
                } else {
                    "此下载核心不可用"
                }
            }
        }

        Text {
            visible: taskData && taskData.creationTime ? true : false
            text: {
                if (visible) {
                    "添加于" + JsUtils.humanTimeElapse(taskData.creationTime)
                } else {
                    ""
                }
            }
        }

        Text {
            visible: taskData && taskData.completionTime ? true : false
            text: {
                if (visible) {
                    "完成于" + JsUtils.humanTimeElapse(taskData.completionTime)
                } else {
                    ""
                }
            }
        }
    }
}
