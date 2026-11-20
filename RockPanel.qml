import QtQuick
import Quickshell
import Quickshell.Io
import qs.Commons
import qs.Ui as Ui

Ui.Panel {
    id: root
    moduleName: "io.github.brokemac79.omarock"
    ipcTarget: "io.github.brokemac79.omarock"
    manageIpc: true
    property var anchorItem: null
    property var hostWidget: null
    property var report: ({})
    property bool stale: true
    property bool fetching: false
    property string lastError: ""
    property string python: ""
    property string base: ""
    property int tab: 0
    property int floor: -1
    property int scope: 0
    property int mode: 0
    property int passes: 1
    property var selected: []
    property var zones: []
    property var draft: null
    property var pending: null
    property bool confirmedFloor: false
    property string actionMessage: ""
    readonly property var maps: report.maps || []
    readonly property var current: maps.find(function(m){return m.id===root.floor}) || ({rooms:[],name:"No floor"})
    readonly property bool activeFloor: floor===report.activeFloor
    readonly property bool writable: report.controlsEnabled===true && !stale && !fetching && !action.running
    readonly property color muted: Qt.rgba(Color.foreground.r,Color.foreground.g,Color.foreground.b,0.6)
    signal refreshRequested()
    onPendingChanged: { if(pending)Qt.callLater(function(){scroller.contentY=Math.max(0,scroller.contentHeight-scroller.height)}) }
    onReportChanged: { if(floor===-1 && report.activeFloor!==undefined)floor=report.activeFloor }
    function label(s) { return String(s===undefined || s===null ? "unknown" : s).replace(/_/g," ") }
    function chooseFloor(id) {floor=id;selected=[];zones=[];draft=null;mapCanvas.requestPaint()}
    function chooseRoom(id) {var a=selected.slice();var n=a.indexOf(id);if(n<0)a.push(id);else a.splice(n,1);selected=a;scope=0}
    function date(s) { return s ? new Date(s*1000).toLocaleString(Qt.locale("en_GB"),"ddd d MMM HH:mm") : "Unknown" }
    function floorName(id) {var m=maps.find(function(x){return x.id===id});return m?m.name:"Unknown floor"}
    function point(x,y) {
        var c=report.calibration
        if(!c || c.length!==3)throw new Error("Map calibration unavailable")
        var a=c[0],b=c[1],d=c[2],ux=b.map.x-a.map.x,uy=b.map.y-a.map.y,vx=d.map.x-a.map.x,vy=d.map.y-a.map.y,det=ux*vy-uy*vx
        if(Math.abs(det)<0.000001)throw new Error("Invalid calibration")
        var p=((x-a.map.x)*vy-(y-a.map.y)*vx)/det,q=(ux*(y-a.map.y)-uy*(x-a.map.x))/det
        return [a.vacuum.x+p*(b.vacuum.x-a.vacuum.x)+q*(d.vacuum.x-a.vacuum.x),a.vacuum.y+p*(b.vacuum.y-a.vacuum.y)+q*(d.vacuum.y-a.vacuum.y)]
    }
    function review() {
        try {
            if(scope===0 && !selected.length)throw new Error("Select at least one room")
            if(scope===2 && !zones.length)throw new Error("Draw a rectangle on the map")
            var converted=[]
            if(scope===2)for(var z of zones){var pts=[point(z[0],z[1]),point(z[0],z[3]),point(z[2],z[1]),point(z[2],z[3])];converted.push([Math.min.apply(null,pts.map(function(p){return p[0]})),Math.min.apply(null,pts.map(function(p){return p[1]})),Math.max.apply(null,pts.map(function(p){return p[0]})),Math.max.apply(null,pts.map(function(p){return p[1]}))])}
            pending={action:"clean",plan:{floor:floor,scope:["rooms","floor","zone"][scope],mode:["vacuum","vacuum_and_mop","mop"][mode],passes:scope===1?1:passes,rooms:selected,zones:converted}}
            confirmedFloor=false;actionMessage=""
        }catch(e){actionMessage=e.message}
    }
    function submit() {
        if(!pending || !writable)return
        if(pending.plan){if(!confirmedFloor)return;pending.plan.confirmedFloor=floor}
        pending.confirmed=true
        action.command=[python,base+"/omarock.py","action","--request",JSON.stringify(pending)]
        action.running=true
    }
    Process {
        id: action
        stdout: StdioCollector { onStreamFinished: {try{var r=JSON.parse(text);root.actionMessage=r.error||r.status;if(!r.error)root.pending=null}catch(e){root.actionMessage="Command outcome unknown. Check the official app before retrying."}} }
        onExited: function(code) { if(code===0)root.refreshRequested() }
    }
    function open() { controller.show(); focusTimer.restart() }
    Timer { id: focusTimer; interval: 150; onTriggered: {catcher.forceActiveFocus(); if(!focusApp.running)focusApp.running=true} }
    Process { id: focusApp; command: ["hyprctl","dispatch",'hl.dsp.focus({ window = "title:^OmaRock$" })'] }
    FloatingWindow {
        id: appWindow
        title: "OmaRock"
        visible: root.opened
        color: Color.background
        implicitWidth: 1280
        implicitHeight: 900
        minimumSize: Qt.size(860, 600)
        onVisibleChanged: { if(!visible && root.opened)root.close() }
        FocusScope {
            id: catcher
            anchors.fill: parent
            focus: true
            Keys.onPressed: function(event) {
                if(event.key===Qt.Key_Escape) { if(root.pending)root.pending=null;else root.close();event.accepted=true }
                else if(event.key===Qt.Key_Right) {root.tab=(root.tab+1)%4;event.accepted=true}
                else if(event.key===Qt.Key_Left) {root.tab=(root.tab+3)%4;event.accepted=true}
                else if(event.key===Qt.Key_R) {root.refreshRequested();event.accepted=true}
                else if(event.key===Qt.Key_H) {root.tab=1;event.accepted=true}
                else if(event.key===Qt.Key_M) {root.tab=2;event.accepted=true}
                else if(event.key===Qt.Key_C) {root.tab=3;event.accepted=true}
                else if(event.key===Qt.Key_O) {root.tab=0;event.accepted=true}
            }
            Rectangle {
                id: sidebar
                anchors {left:parent.left;top:parent.top;bottom:parent.bottom}
                width:180
                color: Qt.rgba(Color.foreground.r,Color.foreground.g,Color.foreground.b,0.025)
                Rectangle {anchors.right:parent.right;width:1;height:parent.height;color:Qt.rgba(Color.foreground.r,Color.foreground.g,Color.foreground.b,0.12)}
                Column {
                    anchors {left:parent.left;right:parent.right;top:parent.top;margins:16;topMargin:30}
                    spacing:12
                    Text {text:"◎  OMAROCK";color:Color.accent;font.family:Style.font.family;font.pixelSize:16;font.bold:true}
                    Text {text:"YOUR HOME, IN VIEW";color:root.muted;font.family:Style.font.family;font.pixelSize:9}
                    Item {width:1;height:20}
                    Repeater {
                        model:["◈ Overview","◷ History","⌁ Maintenance","⚙ Connection"]
                        RockButton {required property string modelData;required property int index;width:148;height:40;text:modelData;selected:root.tab===index;onClicked:{root.tab=index;catcher.forceActiveFocus()}}
                    }
                }
                Column {
                    anchors {left:parent.left;right:parent.right;bottom:parent.bottom;margins:18}
                    spacing:5
                    Text {text:"OMARCHY EDITION";color:root.muted;font.family:Style.font.family;font.pixelSize:10}
                    Text {text:"v0.1.0 · MIT";color:root.muted;font.family:Style.font.family;font.pixelSize:10}
                }
            }
            Flickable {
                id: scroller
                anchors {left:sidebar.right;right:parent.right;top:parent.top;bottom:parent.bottom;margins:24}
                contentWidth: Math.max(width,800)
                contentHeight: body.implicitHeight
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                Column {
                    id: body
                    width: scroller.contentWidth
                    spacing: 16
                    Row {
                        width: parent.width
                        Column {
                            width: parent.width-115
                            spacing: 5
                            Text {text:"◎  OmaRock";font.family:Style.font.family;font.pixelSize:25;font.bold:true;color:Color.foreground}
                            Text {text:(root.report.name||"Roborock companion")+"  ·  NATIVE DESKTOP APP";font.family:Style.font.family;font.pixelSize:10;color:root.muted}
                        }
                        RockButton {text:root.fetching?"Updating…":"Refresh ↻";available:!root.fetching;onClicked:root.refreshRequested()}
                    }
                    Rectangle {
                        width: parent.width
                        height: warning.implicitHeight+22
                        radius: 5
                        color: Qt.rgba(Color.accent.r,Color.accent.g,Color.accent.b,0.12)
                        Text {
                            id: warning
                            anchors{left:parent.left;right:parent.right;verticalCenter:parent.verticalCenter;leftMargin:12;rightMargin:12}
                            text: root.lastError ? root.lastError : !root.report.authPresent ? "Desktop sign-in needed. Showing a timestamped snapshot only; no live connection yet." : root.lastError ? root.lastError : root.stale ? "Cached data is stale. Refresh before relying on robot state." : !root.report.controlsEnabled ? "Read-only safety lock · cleaning controls await supervised commissioning." : "Live connection · review every request before sending."
                            wrapMode: Text.WordWrap
                            color: Color.accent
                            font.family: Style.font.family
                            font.pixelSize: 11
                        }
                    }
                    Column {
                        width: parent.width
                        visible: root.tab===0
                        spacing: 14
                        Row {
                            spacing: 6
                            Repeater {model:root.maps;RockButton {required property var modelData;text:modelData.name+(modelData.id===root.report.activeFloor?" •":"");selected:root.floor===modelData.id;onClicked:root.chooseFloor(modelData.id)}}
                        }
                        Row {
                            width: parent.width
                            spacing: 20
                            Column {
                                width: parent.width-285
                                spacing: 10
                                Rectangle {
                                    width: parent.width
                                    height: Math.min(400,width*0.65)
                                    radius: 7
                                    color: Qt.rgba(Color.foreground.r,Color.foreground.g,Color.foreground.b,0.045)
                                    border.color: Qt.rgba(Color.foreground.r,Color.foreground.g,Color.foreground.b,0.12)
                                    Image {
                                        id: mapImage
                                        anchors.fill: parent
                                        anchors.margins: 8
                                        source: root.activeFloor ? root.report.mapImage || "" : ""
                                        fillMode: Image.PreserveAspectFit
                                        cache: false
                                        onStatusChanged:mapCanvas.requestPaint()
                                    }
                                    Text {
                                        anchors.centerIn:parent
                                        width:parent.width-60
                                        visible:mapImage.status!==Image.Ready
                                        text:root.activeFloor?"No map loaded":"Browsing saved floor. Select this floor in the Roborock app after moving the robot to it."
                                        horizontalAlignment:Text.AlignHCenter
                                        wrapMode:Text.WordWrap
                                        font.family:Style.font.family
                                        font.pixelSize:12
                                        color:root.muted
                                    }
                                    Item {
                                        id: imagePlane
                                        width: mapImage.paintedWidth
                                        height: mapImage.paintedHeight
                                        anchors.centerIn: parent
                                        Canvas {
                                            id:mapCanvas
                                            anchors.fill:parent
                                            onWidthChanged:requestPaint()
                                            onHeightChanged:requestPaint()
                                            onPaint:{
                                                var ctx=getContext("2d");ctx.clearRect(0,0,width,height)
                                                if(!mapImage.sourceSize.width || !mapImage.sourceSize.height)return
                                                var sx=width/mapImage.sourceSize.width,sy=height/mapImage.sourceSize.height
                                                var all=root.zones.slice();if(root.draft)all.push(root.draft)
                                                ctx.strokeStyle=Color.accent;ctx.lineWidth=2;ctx.fillStyle=Qt.rgba(Color.accent.r,Color.accent.g,Color.accent.b,0.22)
                                                for(var z of all){var x=Math.min(z[0],z[2])*sx,y=Math.min(z[1],z[3])*sy,w=Math.abs(z[2]-z[0])*sx,h=Math.abs(z[3]-z[1])*sy;ctx.fillRect(x,y,w,h);ctx.strokeRect(x,y,w,h)}
                                            }
                                        }
                                        MouseArea {
                                            anchors.fill:parent
                                            enabled:root.scope===2 && root.activeFloor && mapImage.status===Image.Ready
                                            cursorShape:Qt.CrossCursor
                                            function p(mouse){return [Math.max(0,Math.min(mapImage.sourceSize.width,mouse.x/width*mapImage.sourceSize.width)),Math.max(0,Math.min(mapImage.sourceSize.height,mouse.y/height*mapImage.sourceSize.height))]}
                                            onPressed:function(mouse){if(root.zones.length>=5){root.actionMessage="Maximum five zones";return};var a=p(mouse);root.draft=[a[0],a[1],a[0],a[1]];mapCanvas.requestPaint()}
                                            onPositionChanged:function(mouse){if(root.draft){var a=p(mouse);root.draft=[root.draft[0],root.draft[1],a[0],a[1]];mapCanvas.requestPaint()}}
                                            onReleased:{if(root.draft && Math.abs(root.draft[2]-root.draft[0])>5 && Math.abs(root.draft[3]-root.draft[1])>5)root.zones=root.zones.concat([root.draft]);root.draft=null;mapCanvas.requestPaint()}
                                            onCanceled:{root.draft=null;mapCanvas.requestPaint()}
                                        }
                                    }
                                }
                                Row {
                                    width:parent.width
                                    Text {width:parent.width-110;text:root.report.mapAt?"Map captured "+new Date(root.report.mapAt).toLocaleTimeString(Qt.locale("en_GB"),"HH:mm"):"Robot-reported map";color:root.muted;font.family:Style.font.family;font.pixelSize:10}
                                    RockButton {text:"Clear zones";onClicked:{root.zones=[];mapCanvas.requestPaint()}}
                                }
                                Flow {
                                    width:parent.width
                                    spacing:6
                                    Repeater {model:root.current.rooms||[];RockButton {required property var modelData;text:modelData.name;selected:root.selected.indexOf(modelData.id)>=0;onClicked:root.chooseRoom(modelData.id)}}
                                }
                            }
                            Column {
                                width:265
                                spacing:12
                                Text {text:root.label(root.report.state);color:Color.foreground;font.family:Style.font.family;font.pixelSize:22}
                                Text {text:root.report.battery===undefined?"—":root.report.battery+"%";color:Color.accent;font.family:Style.font.family;font.pixelSize:36;font.bold:true}
                                Text {text:"Clean water · "+root.label(root.report.cleanWater)+"\nDirty water · "+root.label(root.report.dirtyWater);color:Color.foreground;font.family:Style.font.family;font.pixelSize:11;lineHeight:1.5}
                                Text {width:parent.width;text:"Tank flags, not fill levels.\nWash: "+(root.report.washing===0?"idle":root.label(root.report.washing))+" · Dry: "+(root.report.drying===0?"idle":root.label(root.report.drying));color:root.muted;font.family:Style.font.family;font.pixelSize:10;wrapMode:Text.WordWrap}
                                Row {spacing:5;Repeater {model:["Rooms","Floor","Zone"];RockButton {required property string modelData;required property int index;text:modelData;selected:root.scope===index;onClicked:{root.scope=index;if(index===1)root.passes=1}}}}
                                Text {text:"CLEANING MODE";color:root.muted;font.family:Style.font.family;font.pixelSize:10}
                                Row {spacing:4;Repeater {model:["Vacuum","Both","Mop"];RockButton {required property string modelData;required property int index;text:modelData;selected:root.mode===index;onClicked:root.mode=index}}}
                                Row {
                                    spacing:8
                                    Text {text:"Passes";color:root.muted;font.family:Style.font.family;font.pixelSize:11;anchors.verticalCenter:parent.verticalCenter}
                                    Repeater {model:3;RockButton {required property int index;text:String(index+1);selected:root.passes===index+1;available:root.scope!==1 || index===0;onClicked:root.passes=index+1}}
                                }
                                Text {width:parent.width;text:root.scope===0?root.selected.length+" room(s) selected":root.scope===1?"Whole "+root.current.name:root.zones.length+" zone(s) · drag on map";color:root.muted;font.family:Style.font.family;font.pixelSize:11;wrapMode:Text.WordWrap}
                                RockButton {width:parent.width;text:"Review cleaning request →";primary:true;available:root.activeFloor;onClicked:root.review()}
                                Row {spacing:8;RockButton {text:"Ⅱ Pause";onClicked:{root.pending={action:"pause"};root.actionMessage=""}} RockButton {text:"⌂ Dock";onClicked:{root.pending={action:"dock"};root.actionMessage=""}}}
                                Text {width:parent.width;text:root.report.controlsEnabled?"Supervise first cleaning tests.":"Controls locked. Preview only; no commands sent.";color:root.muted;font.family:Style.font.family;font.pixelSize:10;wrapMode:Text.WordWrap}
                            }
                        }
                    }
                    Column {
                        width:parent.width
                        spacing:10
                        visible:root.tab===1
                        Text {text:"Recent activity";color:Color.foreground;font.family:Style.font.family;font.pixelSize:22}
                        Text {width:parent.width;text:"Floor runs do not prove every room was cleaned. Missing room IDs remain unknown.";color:root.muted;font.family:Style.font.family;font.pixelSize:11;wrapMode:Text.WordWrap}
                        Repeater {
                            model:root.report.history||[]
                            Rectangle {
                                required property var modelData
                                width:body.width
                                height:75
                                radius:5
                                color:Qt.rgba(Color.foreground.r,Color.foreground.g,Color.foreground.b,0.045)
                                Column {anchors{left:parent.left;verticalCenter:parent.verticalCenter;leftMargin:14} spacing:7
                                    Text {text:root.floorName(modelData.map_flag)+" · "+root.date(modelData.begin);color:Color.foreground;font.family:Style.font.family;font.pixelSize:12}
                                    Text {text:(modelData.area/1000000).toFixed(1)+" m² · "+Math.round(modelData.duration/60)+" min · "+(modelData.complete===1?"Complete":"Completion unconfirmed")+" · Rooms "+((modelData.area_ids||[]).length?modelData.area_ids.join(", "):"unknown");color:root.muted;font.family:Style.font.family;font.pixelSize:10}
                                }
                            }
                        }
                    }
                    Column {
                        width:parent.width
                        spacing:12
                        visible:root.tab===2
                        Text {text:"A little care.";color:Color.foreground;font.family:Style.font.family;font.pixelSize:22}
                        Repeater {model:[{key:"main_brush",name:"Main brush"},{key:"side_brush",name:"Side brush"},{key:"filter",name:"Filter"},{key:"sensor",name:"Sensors"}];Rectangle {
                            required property var modelData
                            width:body.width;height:65;radius:5;color:Qt.rgba(Color.foreground.r,Color.foreground.g,Color.foreground.b,0.045)
                            Text {anchors{left:parent.left;verticalCenter:parent.verticalCenter;leftMargin:14} text:modelData.name;color:Color.foreground;font.family:Style.font.family;font.pixelSize:13}
                            Text {anchors{right:parent.right;verticalCenter:parent.verticalCenter;rightMargin:14} text:root.report.consumables && root.report.consumables[modelData.key]!==null?root.report.consumables[modelData.key]+" h remaining":"Unknown";color:Color.accent;font.family:Style.font.family;font.pixelSize:13}
                        }}
                        Text {text:"Library estimates based on usage—not physical condition sensors.";color:root.muted;font.family:Style.font.family;font.pixelSize:10}
                    }
                    Column {
                        width:parent.width
                        spacing:15
                        visible:root.tab===3
                        Text {text:"Your Roborock, on your desktop.";color:Color.foreground;font.family:Style.font.family;font.pixelSize:22}
                        Text {width:parent.width;text:"This is a separate native app window, opened from the application launcher or bar icon. Resize, tile or move it between workspaces like any other app. A private Python helper talks to Roborock. No browser, WebView or web server.";color:Color.foreground;font.family:Style.font.family;font.pixelSize:12;wrapMode:Text.WordWrap}
                        Text {width:parent.width;text:"Sign in once on this machine using the library’s email-code login:\n\n~/.local/share/omarock/venv/bin/roborock login --email YOUR_EMAIL\n\nThen click Refresh. Credentials stay in ~/.roborock, outside the repository.";color:root.muted;font.family:Style.font.family;font.pixelSize:12;wrapMode:Text.WrapAnywhere}
                        Text {width:parent.width;text:"Current limitations: only the current floor image is available; other floor maps must be selected in the official app after moving the robot. Room freshness is not inferred from incomplete history. Cleaning/mode/zone control awaits supervised Saros 20 testing.";color:root.muted;font.family:Style.font.family;font.pixelSize:12;wrapMode:Text.WordWrap}
                    }
                    Rectangle {
                        width:parent.width
                        height:reviewBody.implicitHeight+28
                        visible:!!root.pending
                        radius:6
                        color:Qt.rgba(Color.accent.r,Color.accent.g,Color.accent.b,0.13)
                        border.color:Color.accent
                        Column {
                            id:reviewBody
                            anchors{left:parent.left;right:parent.right;top:parent.top;margins:14}
                            spacing:12
                            Text {text:root.pending && root.pending.plan?"Review: "+root.current.name+" · "+["Rooms","Whole floor","Zone"][root.scope]+" · "+["Vacuum","Vacuum & mop","Mop"][root.mode]:"Confirm: "+(root.pending?root.pending.action:"");color:Color.foreground;font.family:Style.font.family;font.pixelSize:14}
                            RockButton {visible:!!root.pending && !!root.pending.plan;text:(root.confirmedFloor?"✓ ":"□ ")+"Robot is physically on "+root.current.name;selected:root.confirmedFloor;onClicked:root.confirmedFloor=!root.confirmedFloor}
                            Text {text:root.writable?"This will operate your robot. Supervise the first test.":"Safety lock or stale state: preview only. No device command can be sent.";color:Color.accent;font.family:Style.font.family;font.pixelSize:11}
                            Row {spacing:10;RockButton {text:"Cancel";onClicked:root.pending=null} RockButton {text:action.running?"Sending…":"Send to robot";primary:true;available:root.writable && (!root.pending || !root.pending.plan || root.confirmedFloor);onClicked:root.submit()}}
                        }
                    }
                    Text {width:parent.width;text:root.actionMessage;visible:text!=="";color:Color.accent;font.family:Style.font.family;font.pixelSize:12;wrapMode:Text.WordWrap}
                    Text {text:"OmaRock 0.1.0 · Independent community plugin · MIT";color:root.muted;font.family:Style.font.family;font.pixelSize:10}
                }
            }
        }
    }
}
