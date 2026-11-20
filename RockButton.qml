import QtQuick
import qs.Commons
Rectangle {
    id: root
    property string text: ""
    property bool selected: false
    property bool primary: false
    property bool available: true
    signal clicked()
    activeFocusOnTab: root.available
    Accessible.role: Accessible.Button
    Accessible.name: root.text
    Accessible.onPressAction: {if(root.available)root.clicked()}
    Keys.onPressed: function(event) {if(root.available && (event.key===Qt.Key_Return || event.key===Qt.Key_Enter || event.key===Qt.Key_Space)){root.clicked();event.accepted=true}}
    implicitWidth: label.implicitWidth+24
    implicitHeight: 34
    radius: 5
    color: primary || selected ? Color.accent : mouse.containsMouse ? Qt.rgba(Color.foreground.r,Color.foreground.g,Color.foreground.b,0.12) : Qt.rgba(Color.foreground.r,Color.foreground.g,Color.foreground.b,0.055)
    border.width: 1
    border.color: primary || selected ? Color.accent : Qt.rgba(Color.foreground.r,Color.foreground.g,Color.foreground.b,0.14)
    opacity: available ? 1 : 0.4
    Text { id: label; anchors.centerIn: parent; text: root.text; color: root.primary || root.selected ? Color.background : Color.foreground; font.family: Style.font.family; font.pixelSize: 12 }
    MouseArea { id: mouse; anchors.fill: parent; hoverEnabled: true; enabled: root.available; onClicked: {root.forceActiveFocus();root.clicked()} }
}
