import QtQuick
import Quickshell
import Quickshell.Io
import qs.Commons
import qs.Ui as Ui

Ui.BarWidget {
    id: root
    moduleName: "io.github.brokemac79.omarock"
    property var report: ({})
    property double clock: Date.now()
    readonly property string base: decodeURIComponent(Qt.resolvedUrl(".").toString().replace(/^file:\/\//, "")).replace(/\/$/, "")
    readonly property bool stale: !report.at || clock-Date.parse(report.at)>180000
    implicitWidth: button.implicitWidth
    implicitHeight: button.implicitHeight
    Process {
        id: reader
        command: ["python3", root.base+"/omarock.py", "bar"]
        stdout: StdioCollector { onStreamFinished: { try { root.report=JSON.parse(text) } catch(e) { root.report=({}) } } }
    }
    Process { id: launcher; command: [root.base+"/.venv/bin/python", root.base+"/omarock.py", "open"] }
    Timer { interval: 15000; repeat: true; running: true; triggeredOnStart: true; onTriggered: {root.clock=Date.now(); if(!reader.running) reader.running=true} }
    Ui.WidgetButton {
        id: button
        anchors.fill: parent
        bar: root.bar
        text: "󰤄 " + (root.stale ? "—" : root.report.battery+"%")
        tooltipText: "OmaRock · "+(root.stale ? "Offline / stale — open to connect" : root.report.state+" · Clean water: "+root.report.cleanWater)
        onPressed: function(b) { if(!launcher.running) launcher.running=true }
    }
}
