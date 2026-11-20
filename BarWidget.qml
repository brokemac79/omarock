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
    property string lastError: ""
    readonly property string base: decodeURIComponent(Qt.resolvedUrl(".").toString().replace(/^file:\/\//, "")).replace(/\/$/, "")
    readonly property string python: (Quickshell.env("XDG_DATA_HOME") || Quickshell.env("HOME")+"/.local/share")+"/omarock/venv/bin/python"
    readonly property bool stale: !report.at || clock-Date.parse(report.at)>180000
    readonly property bool opened: panel.opened
    readonly property bool popoutSwitchClosing: panel.popoutSwitchClosing
    implicitWidth: button.implicitWidth
    implicitHeight: button.implicitHeight
    function open() { panel.open(); refresh() }
    function close() { panel.close() }
    function toggle() { opened ? close() : open() }
    function closeForPopoutSwitch() { panel.closeForPopoutSwitch() }
    function refresh() { if(!fetcher.running && report.authPresent) fetcher.running=true; else if(!reader.running) reader.running=true }
    Process {
        id: reader
        command: ["python3",root.base+"/omarock.py","cached"]
        stdout: StdioCollector { onStreamFinished: { try { var r=JSON.parse(text); if(!r.error)root.report=r;else root.lastError=r.error } catch(e) { root.lastError="Cannot read cached status" } } }
    }
    Process {
        id: fetcher
        command: [root.python,root.base+"/omarock.py","snapshot"]
        stdout: StdioCollector { onStreamFinished: { try { var r=JSON.parse(text); if(r.error)root.lastError=r.error;else {r.authPresent=true;root.report=r;root.lastError=""} } catch(e) { root.lastError="Refresh failed" } } }
    }
    Timer { interval: root.opened ? 60000 : 120000; running: true; repeat: true; triggeredOnStart: true; onTriggered: {root.clock=Date.now();root.refresh()} }
    Ui.WidgetButton {
        id: button
        anchors.fill: parent
        bar: root.bar
        text: "󰤄 "+(root.stale ? "—" : root.report.battery+"%")
        tooltipText: "OmaRock · "+(root.stale ? "Cached / stale" : root.report.state)+" · click to open native panel"
        onPressed: function(b) { if(b===Qt.MiddleButton)root.refresh();else root.toggle() }
    }
    RockPanel {
        id: panel
        bar: root.bar
        settings: root.settings
        anchorItem: button
        hostWidget: root
        report: root.report
        stale: root.stale
        fetching: fetcher.running
        lastError: root.lastError
        python: root.python
        base: root.base
        onRefreshRequested: root.refresh()
    }
}
