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
    onTabChanged: {if(tab===4 && !planReader.running)planReader.running=true}
    property int floor: -1
    property int scope: 0
    property int mode: 0
    property int passes: 1
    property var selected: []
    property bool showPath: true
    property bool showObstacles: true
    property bool showRestrictions: true
    property var zones: []
    property var draft: null
    property var pending: null
    property bool confirmedFloor: false
    property string actionMessage: ""
    readonly property var maps: report.maps || []
    readonly property var current: maps.find(function(m){return m.id===root.floor}) || ({rooms:[],name:"No floor"})
    readonly property bool activeFloor: floor===report.activeFloor
    readonly property bool writable: report.controlsEnabled===true && !stale && !fetching && !action.running && !importing
    readonly property color muted: Qt.rgba(Color.foreground.r,Color.foreground.g,Color.foreground.b,0.6)
    signal refreshRequested()
    signal signedIn()
    signal mapsImported(var value)
    readonly property bool importing: importer.running
    readonly property var floorMap: (report.floorMaps || {})[String(floor)] || (activeFloor ? report : ({}))
    readonly property bool authActive: loginForm.authActive
    onOpenedChanged: {if(!opened && loginForm.authActive)loginForm.cancel()}
    onPendingChanged: { if(pending)Qt.callLater(function(){scroller.contentY=Math.max(0,scroller.contentHeight-scroller.height)}) }
    onReportChanged: { if(floor===-1 && report.activeFloor!==undefined)floor=report.activeFloor; if(tab===4 && !planReader.running)planReader.running=true }
    function label(s) { return String(s===undefined || s===null ? "unknown" : s).replace(/_/g," ") }
    function chooseFloor(id) {floor=id;selected=[];zones=[];draft=null;mapCanvas.requestPaint()}
    function chooseRoom(id) {var a=selected.slice();var n=a.indexOf(id);if(n<0)a.push(id);else a.splice(n,1);selected=a;scope=0}
    function date(s) { return s ? new Date(s*1000).toLocaleString(Qt.locale("en_GB"),"ddd d MMM HH:mm") : "Unknown" }
    function floorName(id) {var m=maps.find(function(x){return x.id===id});return m?m.name:"Unknown floor"}
    function point(x,y) {
        var c=floorMap.calibration
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
        if(pending.routine && pending.routine.reviewed!==true)return
        if(pending.action==="clean" && pending.plan){if(!confirmedFloor)return;pending.plan.confirmedFloor=floor}
        pending.confirmed=true
        action.command=[python,base+"/omarock.py","action","--request",JSON.stringify(pending)]
        action.running=true
    }
    Process {
        id: action
        stdout: StdioCollector { onStreamFinished: {try{var r=JSON.parse(text);root.actionMessage=r.error||r.status;if(!r.error)root.pending=null}catch(e){root.actionMessage="Command outcome unknown. Check the official app before retrying."}} }
        onExited: function(code) { if(code===0)root.refreshRequested() }
    }
    Process {
        id: importer
        command: [root.python,root.base+"/omarock.py","import-maps","--request",'{"confirmed":true}']
        stdout: StdioCollector { onStreamFinished: {try {var value=JSON.parse(text);root.actionMessage=value.error || value.importMessage;if(!value.error)root.mapsImported(value)} catch(e) {root.actionMessage="Map import outcome unknown. Check the selected floor in the official app."}} }
    }
    Process {
        id: planReader
        command: [root.python,root.base+"/omarock.py","planner"]
        stdout: StdioCollector {onStreamFinished:{try{schedule.rows=JSON.parse(text).rows||[]}catch(e){root.actionMessage="Cannot read cleaning plans"}}}
    }
    function open() { if(!report.authPresent)tab=3;controller.show(); focusTimer.restart() }
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
                else if(event.key===Qt.Key_End) {scroller.contentY=Math.max(0,scroller.contentHeight-scroller.height);event.accepted=true}
                else if(event.key===Qt.Key_Home) {scroller.contentY=0;event.accepted=true}
                else if(event.key===Qt.Key_Right) {root.tab=(root.tab+1)%6;event.accepted=true}
                else if(event.key===Qt.Key_Left) {root.tab=(root.tab+5)%6;event.accepted=true}
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
                        model:["◈ Overview","◷ History","⌁ Maintenance","⚙ Connection","▤ Timeline","◷ Schedules"]
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
                anchors {left:sidebar.right;right:parent.right;top:parent.top;bottom:parent.bottom;margins:16}
                contentWidth: Math.max(width,800)
                contentHeight: body.implicitHeight+24
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                Column {
                    id: body
                    width: scroller.contentWidth
                    spacing: 10
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
                            text: root.lastError ? root.lastError : !root.report.authPresent ? "Sign in under Connection to load live robot data. Cached map/status below are not live." : root.lastError ? root.lastError : root.stale ? "Cached data is stale. Refresh before relying on robot state." : !root.report.controlsEnabled ? "Read-only safety lock · cleaning controls await supervised commissioning." : "Live connection · review every request before sending."
                            wrapMode: Text.WordWrap
                            color: Color.accent
                            font.family: Style.font.family
                            font.pixelSize: 11
                        }
                    }
                    Column {
                        width: parent.width
                        visible: root.tab===0
                        spacing: 8
                        Row {
                            spacing: 6
                            RockButton {text:root.importing?"Importing…":"Import all floors";available:!root.fetching && !root.importing && !root.authActive && !action.running && !!root.report.authPresent;onClicked:root.pending={action:"import-maps"}}
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
                                    height: Math.min(360,width*0.65,Math.max(210,scroller.height-245))
                                    radius: 7
                                    color: Qt.rgba(Color.foreground.r,Color.foreground.g,Color.foreground.b,0.045)
                                    border.color: Qt.rgba(Color.foreground.r,Color.foreground.g,Color.foreground.b,0.12)
                                    Image {
                                        id: mapImage
                                        anchors.fill: parent
                                        anchors.margins: 8
                                        source: root.floorMap.mapImage || ""
                                        fillMode: Image.PreserveAspectFit
                                        cache: false
                                        onStatusChanged:mapCanvas.requestPaint()
                                    }
                                    Text {
                                        anchors.centerIn:parent
                                        width:parent.width-60
                                        visible:mapImage.status!==Image.Ready
                                        text:"No cached map for this floor. Use Import all floors while the robot is idle."
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
                                                var layers=root.floorMap.layers||{}
                                                function line(points,color,closed){if(!points.length)return;ctx.beginPath();ctx.moveTo(points[0][0]*sx,points[0][1]*sy);for(var i=1;i<points.length;i++)ctx.lineTo(points[i][0]*sx,points[i][1]*sy);if(closed)ctx.closePath();ctx.strokeStyle=color;ctx.lineWidth=2;ctx.stroke()}
                                                if(root.showPath)for(var path of (layers.path||[]))line(path.points,path.kind==="mop_path"?"#55ccee":"#f2d77a",false)
                                                if(root.showRestrictions)for(var area of (layers.restrictions||[]))line(area.points,"#ff7676",area.points.length>2)
                                                if(root.showObstacles)for(var obstacle of (layers.obstacles||[])){ctx.beginPath();ctx.arc(obstacle[0]*sx,obstacle[1]*sy,4,0,Math.PI*2);ctx.fillStyle="#ff9944";ctx.fill()}
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
                                    Text {width:parent.width-110;text:root.floorMap.mapAt?"Map captured "+new Date(root.floorMap.mapAt).toLocaleTimeString(Qt.locale("en_GB"),"HH:mm"):"Robot-reported map";color:root.muted;font.family:Style.font.family;font.pixelSize:10}
                                    RockButton {text:"Clear zones";onClicked:{root.zones=[];mapCanvas.requestPaint()}}
                                }
                                Flow {
                                    width:parent.width;spacing:6
                                    RockButton {text:"Path";available:!!root.floorMap.layers && root.floorMap.layers.path.length>0;selected:root.showPath;onClicked:{root.showPath=!root.showPath;mapCanvas.requestPaint()}}
                                    RockButton {text:"Obstacles";available:!!root.floorMap.layers && root.floorMap.layers.obstacles.length>0;selected:root.showObstacles;onClicked:{root.showObstacles=!root.showObstacles;mapCanvas.requestPaint()}}
                                    RockButton {text:"Restrictions";available:!!root.floorMap.layers && root.floorMap.layers.restrictions.length>0;selected:root.showRestrictions;onClicked:{root.showRestrictions=!root.showRestrictions;mapCanvas.requestPaint()}}
                                }
                                Text {width:parent.width;text:"Layers: captured vendor geometry only; disabled = no data. Carpet raster unavailable. Colours are not coverage evidence.";color:root.muted;font.family:Style.font.family;font.pixelSize:10;wrapMode:Text.WordWrap}
                                Flow {
                                    width:parent.width
                                    spacing:6
                                    Repeater {model:root.current.rooms||[];RockButton {required property var modelData;text:modelData.name;selected:root.selected.indexOf(modelData.id)>=0;onClicked:root.chooseRoom(modelData.id)}}
                                }
                            }
                            Column {
                                width:265
                                spacing:6
                                Text {text:root.label(root.report.state);color:Color.foreground;font.family:Style.font.family;font.pixelSize:22}
                                Text {text:root.report.battery===undefined?"—":root.report.battery+"%";color:Color.accent;font.family:Style.font.family;font.pixelSize:28;font.bold:true}
                                Text {text:"Clean water · "+root.label(root.report.cleanWater)+"\nDirty water · "+root.label(root.report.dirtyWater);color:Color.foreground;font.family:Style.font.family;font.pixelSize:11;lineHeight:1.2}
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
                        width:parent.width;visible:root.tab===0;spacing:8
                        Text {text:"Saved Roborock routines";color:Color.foreground;font.family:Style.font.family;font.pixelSize:18}
                        Text {width:parent.width;text:root.report.routinesAvailable ? ((root.report.routines||[]).length ? "Review steps and physical floor in the official app before requesting a routine. Routine steps are not available here." : "No saved routines on this device.") : "Routines unavailable. Refresh to retry.";color:root.muted;font.family:Style.font.family;font.pixelSize:11;wrapMode:Text.WordWrap}
                        Flow {width:parent.width;spacing:6
                            Repeater {model:root.report.routines||[]
                                RockButton {required property var modelData;text:"Review: "+modelData.name;onClicked:{root.pending={action:"routine",routine:{id:modelData.id,reviewed:false},routineName:modelData.name};root.actionMessage=""}}
                            }
                        }
                    }
                    RoomPreferences {
                        width:parent.width;visible:root.tab===0
                        python:root.python;base:root.base;floor:root.floor;rooms:root.current.rooms||[]
                        onUseDefault:function(roomId,cleanMode){root.selected=[roomId];root.scope=0;root.mode=cleanMode==="mop"?2:cleanMode==="vacuum_and_mop"?1:0;root.review()}
                    }
                    HistoryPane {width:parent.width;visible:root.tab===1;records:root.report.historyArchive||root.report.history||[];maps:root.maps}
                    Column {
                        width:parent.width
                        spacing:12
                        visible:root.tab===2
                        Text {text:"A little care.";color:Color.foreground;font.family:Style.font.family;font.pixelSize:22}
                        Repeater {model:[{key:"main_brush",name:"Main brush"},{key:"side_brush",name:"Side brush"},{key:"filter",name:"Filter"},{key:"sensor",name:"Sensors"}];Rectangle {
                            required property var modelData
                            width:body.width;height:100;radius:5;color:Qt.rgba(Color.foreground.r,Color.foreground.g,Color.foreground.b,0.045)
                            Text {anchors{left:parent.left;verticalCenter:parent.verticalCenter;leftMargin:14} text:modelData.name;color:Color.foreground;font.family:Style.font.family;font.pixelSize:13}
                            Text {anchors{right:parent.right;verticalCenter:parent.verticalCenter;rightMargin:14} text:root.report.consumables && root.report.consumables[modelData.key]!==undefined && root.report.consumables[modelData.key]!==null?root.report.consumables[modelData.key]+" h remaining"+(root.report.maintenance && root.report.maintenance[modelData.key] && root.report.maintenance[modelData.key].percent!==null?" · "+root.report.maintenance[modelData.key].percent+"%":""):"Unknown";color:Color.accent;font.family:Style.font.family;font.pixelSize:13}
                            RockButton {
                                anchors {left:parent.left;bottom:parent.bottom;margins:12}
                                text:"Reset after "+(modelData.key==="sensor"?"cleaning":"replacement")+"…"
                                available:!!root.report.maintenance && !!root.report.maintenance[modelData.key] && root.report.maintenance[modelData.key].supported
                                onClicked:{root.pending={action:"reset-consumable",plan:{consumable:modelData.key,afterReplacement:true}};root.actionMessage="Only confirm after actual replacement or sensor cleaning. This resets usage, not physical condition."}
                            }
                        }}
                        Text {text:"Library estimates based on usage—not physical condition sensors.";color:root.muted;font.family:Style.font.family;font.pixelSize:10}
                    }
                    Column {
                        width:parent.width
                        spacing:15
                        visible:root.tab===3
                        Text {text:"Your Roborock, on your desktop.";color:Color.foreground;font.family:Style.font.family;font.pixelSize:22}
                        Text {width:parent.width;text:"This is a separate native app window, opened from the application launcher or bar icon. Resize, tile or move it between workspaces like any other app. A private Python helper talks to Roborock. No browser, WebView or web server.";color:Color.foreground;font.family:Style.font.family;font.pixelSize:12;wrapMode:Text.WordWrap}
                        LoginPane {
                            id: loginForm
                            width:parent.width
                            python:root.python
                            base:root.base
                            signedInAlready:root.report.authPresent===true
                            refreshing:root.fetching
                            onSignedIn:{root.signedIn();root.tab=0}
                        }
                        Text {width:parent.width;text:"Import all floors caches saved map images while idle and restores the original map selection. Browsing cached floors never switches the robot. Cleaning still requires the robot’s active map and physical-floor confirmation. Room freshness is not inferred from incomplete history. Cleaning/mode/zone control awaits supervised Saros 20 testing.";color:root.muted;font.family:Style.font.family;font.pixelSize:12;wrapMode:Text.WordWrap}
                    }
                    Column {
                        width:parent.width;spacing:10;visible:root.tab===3
                        Text {text:"DEVICE SETTINGS";color:Color.foreground;font.family:Style.font.family;font.pixelSize:16}
                        Text {width:parent.width;text:"Every change needs review and the safety lock. DND uses the robot’s existing time window; edit that window in the official app. Times are robot-local.";color:root.muted;wrapMode:Text.WordWrap;font.pixelSize:11}
                        Repeater {
                            model:["volume","dnd","child_lock"]
                            Column {
                                required property string modelData
                                property var setting:(root.report.deviceSettings||{})[modelData]
                                width:parent.width;spacing:5
                                Text {text:parent.modelData.replace(/_/g," ")+" · "+(!parent.setting?"Unavailable":parent.modelData==="volume"?parent.setting.value+"%":parent.setting.value?"On":"Off");color:Color.foreground;font.pixelSize:13}
                                Text {visible:parent.modelData==="dnd" && !!parent.setting;text:parent.setting?"Window "+parent.setting.startHour+":"+String(parent.setting.startMinute).padStart(2,"0")+" – "+parent.setting.endHour+":"+String(parent.setting.endMinute).padStart(2,"0"):"";color:root.muted;font.pixelSize:11}
                                Row {
                                    spacing:6
                                    Repeater {
                                        model:modelData==="volume"?[0,25,50,75,100]:[true,false]
                                        RockButton {
                                            required property var modelData
                                            text:typeof modelData==="number"?"Review "+modelData+"%":"Review "+(modelData?"On":"Off")
                                            available:!!parent.parent.setting
                                            onClicked:{root.pending={action:"setting",plan:{setting:parent.parent.modelData,value:modelData,reviewed:true}};root.actionMessage=""}
                                        }
                                    }
                                }
                            }
                        }
                    }
                    Column {
                        width:parent.width;spacing:8;visible:root.tab===3
                        Text {text:"CLEANING PREFERENCES";color:Color.foreground;font.pixelSize:16}
                        Text {width:parent.width;text:"Model-reported options only. Changes require review and the safety lock; physical effect is untested. These are robot-wide preferences, not per-room overrides.";color:root.muted;font.pixelSize:11;wrapMode:Text.WordWrap}
                        Repeater {
                            model:["suction","water","mop_route"]
                            Column {
                                required property string modelData
                                property string preferenceKey:modelData
                                property var setting:(root.report.cleaningSettings||{})[modelData]
                                width:parent.width;spacing:5
                                Text {text:parent.preferenceKey.replace(/_/g," ")+" · "+(parent.setting?parent.setting.options.filter(function(o){return o.value===parent.setting.value}).map(function(o){return o.label}).join(""):"Unavailable");color:Color.foreground;font.pixelSize:13}
                                Flow {
                                    width:parent.width;spacing:6
                                    Repeater {
                                        model:parent.parent.setting?parent.parent.setting.options:[]
                                        RockButton {
                                            required property var modelData
                                            text:"Review "+modelData.label
                                            onClicked:{root.pending={action:"cleaning-setting",plan:{setting:parent.parent.preferenceKey,value:modelData.value,reviewed:true}};root.actionMessage=""}
                                        }
                                    }
                                }
                            }
                        }
                    }
                    Column {
                        width:parent.width;spacing:8;visible:root.tab===3
                        Text {text:"DOCK CYCLES";color:Color.foreground;font.pixelSize:16}
                        Text {width:parent.width;text:"Model-declared capabilities, physically untested. Robot must be charging at dock with no warnings. Every cycle requires review and the safety lock.";color:root.muted;wrapMode:Text.WordWrap;font.pixelSize:11}
                        Flow {width:parent.width;spacing:6
                            Repeater {model:["wash","stop_wash","empty","stop_empty","dry","stop_dry"]
                                RockButton {required property string modelData;text:"Review "+modelData.replace(/_/g," ");available:(root.report.dockControls||{})[modelData]===true;onClicked:{root.pending={action:"dock-cycle",plan:{cycle:modelData,reviewed:true}};root.actionMessage=""}}
                            }
                        }
                    }
                    TimedSchedules {width:parent.width;visible:root.tab===5;python:root.python;base:root.base;maps:root.maps}
                    SchedulePane {
                        id: schedule
                        width:parent.width
                        visible:root.tab===4
                        python:root.python
                        base:root.base
                        viewportHeight:scroller.height-160
                        onEditingChanged:{if(editing)Qt.callLater(function(){scroller.contentY=Math.max(0,scroller.contentHeight-scroller.height)})}
                        onCleanRequested:function(floorId,roomId,cleanMode){root.chooseFloor(floorId);root.scope=roomId===null?1:0;root.selected=roomId===null?[]:[roomId];root.mode=cleanMode==="mop"?2:0;root.tab=0;root.actionMessage="Review the active map and physical floor before cleaning."}
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
                            Text {text:root.pending && root.pending.action==="clean"?"Review: "+root.current.name+" · "+["Rooms","Whole floor","Zone"][root.scope]+" · "+["Vacuum","Vacuum & mop","Mop"][root.mode]:root.pending && (root.pending.action==="setting" || root.pending.action==="cleaning-setting")?"Review setting: "+root.pending.plan.setting+" → "+root.pending.plan.value:root.pending && root.pending.action==="dock-cycle"?"Review dock cycle: "+root.pending.plan.cycle:"Confirm: "+(root.pending?root.pending.action+(root.pending.action==="reset-consumable"?" · "+root.pending.plan.consumable+" · I have replaced/cleaned this part":""):"");color:Color.foreground;font.family:Style.font.family;font.pixelSize:14}
                            RockButton {visible:!!root.pending && root.pending.action==="clean";text:(root.confirmedFloor?"✓ ":"□ ")+"Robot is physically on "+root.current.name;selected:root.confirmedFloor;onClicked:root.confirmedFloor=!root.confirmedFloor}
                            Text {text:root.pending && root.pending.action==="import-maps"?"While idle: briefly select each saved map, cache its image, then restore the original selection. No cleaning.":root.writable?"This will operate your robot. Supervise the first test.":"Safety lock or stale state: preview only. No device command can be sent.";color:Color.accent;font.family:Style.font.family;font.pixelSize:11}
                            RockButton {visible:!!root.pending && !!root.pending.routine;text:((root.pending && root.pending.routine && root.pending.routine.reviewed)?"✓ ":"□ ")+"I checked routine steps and physical floor in the official app";onClicked:{var p=root.pending;p.routine.reviewed=!p.routine.reviewed;root.pending=null;root.pending=p}}
                            Row {spacing:10;RockButton {text:"Cancel";onClicked:root.pending=null} RockButton {text:root.pending && root.pending.action==="import-maps"?"Import maps":action.running?"Sending…":"Send to robot";primary:true;available:root.pending && root.pending.action==="import-maps"?!root.fetching && !root.importing:root.writable && (!root.pending || root.pending.action!=="clean" || root.confirmedFloor);onClicked:{if(root.pending.action==="import-maps"){root.pending=null;root.actionMessage="Importing saved floors…";importer.running=true}else root.submit()}}}
                        }
                    }
                    Text {width:parent.width;text:root.actionMessage;visible:text!=="";color:Color.accent;font.family:Style.font.family;font.pixelSize:12;wrapMode:Text.WordWrap}
                    Text {text:"OmaRock 0.1.0 · Independent community plugin · MIT";color:root.muted;font.family:Style.font.family;font.pixelSize:10}
                }
            }
        }
    }
}
