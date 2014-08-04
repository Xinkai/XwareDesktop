import QtQuick 2.2
import QtQuick.Controls 1.1

Item {
    SplitView {
        anchors.fill: parent
        TableView {
            width: parent.width * 0.7
            model: schedulerModel
            headerVisible: false
            selectionMode: SelectionMode.ExtendedSelection
            TableViewColumn {
                role: "display"
            }
        }
        SchedulerSidebar {
            width: parent.width * 0.3
        }
    }


}
