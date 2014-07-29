import QtQuick 2.2

Rectangle {
    property string title: ""
    width: 100
    height: 62
    color: "steelblue"
    anchors.horizontalCenter: parent.horizontalCenter
    Text {
        text: title
        anchors.fill: parent
        font.pixelSize: 24
        verticalAlignment: Text.AlignVCenter
        horizontalAlignment: Text.AlignHCenter
    }
}
