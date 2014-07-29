import QtQuick 2.2
import QtQuick.Controls 1.1

Rectangle {
    anchors.fill: parent

    Rectangle {
        id: sections
        width: 150

        anchors {
            top: parent.top
            bottom: parent.bottom
            left: parent.left
        }
        color: "lightblue"

        Column {
            anchors {
                fill: parent
                topMargin: 10
            }
            spacing: 10

            SectionSelector {
                title: "一般"
            }

            SectionSelector {
                title: "外观"
            }

            SectionSelector {
                title: "后端"
            }
        }
    }

    AdaptersSection {
        anchors {
            top: parent.top
            bottom: btnGroup.top
            left: sections.right
            right: parent.right
        }
    }

    Rectangle {
        id: btnGroup
        anchors {
            left: sections.right
            bottom: parent.bottom
            right: parent.right
        }
        height: 30
        color: "teal"

        Row {
            anchors {
                fill: parent
            }
            spacing: 8

            Button {
                text: "OK"
            }

            Button {
                text: "Cancel"
            }
        }
    }
}
