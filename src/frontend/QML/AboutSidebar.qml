import QtQuick 2.2
import QtQuick.Controls 1.1

Rectangle {
    anchors.fill: parent
    Column {
        Text {
            horizontalAlignment: Qt.AlignCenter
            width: parent.width
            text: "关于Xware Desktop"
        }

        Text {
            text: "Xware Desktop的下一代界面，不再使用嵌套官方的WebUI。<br />
                   本界面完成后，将有以下变化。<br />
                   <ul>
                       <li>数据不再通过迅雷服务器转发，本机/局域网内可以做到极低延迟。因此也不再支持管理任意远程的Xware实例。</li>
                       <li>可利用QML做出绚丽的视觉效果。</li>
                       <li>可避免官方WebUI的bug。如任务属性为空白、不能缩放尺寸等问题。</li>
                       <li>可支持官方WebUI中没有的功能。如按某种特定顺序显示任务、搜索任务等功能。</li>
                       <li>可支持其它下载核心。如aria2。</li>
                   </ul>"
        }
    }
}
