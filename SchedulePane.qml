import QtQuick
import Quickshell.Io
import qs.Commons

Column {
    id: root
    property string python
    property string base
    property var rows: []
    property int filterFloor: -1
    property var editing: null
    property int intervalDays: 7
    property string message: ""
    property real viewportHeight: 440
    property var expanded: ({})
    signal cleanRequested(var floorId,var roomId,string cleanMode)
    spacing:12
    Text {text:"Cleaning rhythm";color:Color.foreground;font.family:Style.font.family;font.pixelSize:24;font.bold:true}
    Text {width:parent.width;text:"Expand a floor to see its rooms. Past activity ← Today → future reminder dates. Real timed jobs are under Schedules.";color:Color.accent;font.family:Style.font.family;font.pixelSize:11;wrapMode:Text.WordWrap}
    Flow {
        width:parent.width;spacing:6
        RockButton {text:"All floors";selected:root.filterFloor===-1;onClicked:root.filterFloor=-1}
        Repeater {model:root.rows.filter(function(r){return r.room===null});RockButton {required property var modelData;text:modelData.floorName;selected:root.filterFloor===modelData.floor;onClicked:root.filterFloor=modelData.floor}}
    }
    Item {
        width:parent.width;height:20
        Item {
            x:62;width:Math.max(120,root.width-365);height:20
            Repeater {model:["−7d","−3d","TODAY","+3d","+7d"];Text {required property string modelData;required property int index;x:index*(parent.width-30)/4;width:40;text:modelData;color:Color.accent;font.family:Style.font.family;font.pixelSize:10}}
        }
    }
    Flickable {
        id: roomScroll
        width:parent.width
        height:Math.max(160,root.viewportHeight-150-(root.editing?130:0))
        clip:true
        contentWidth:width
        contentHeight:cards.implicitHeight
        boundsBehavior:Flickable.StopAtBounds
        Column {
            id:cards
            width:parent.width
            spacing:8
    Repeater {
        model:root.rows.filter(function(r){return (root.filterFloor===-1 || root.filterFloor===r.floor) && (r.room===null || root.expanded[String(r.floor)]===true)})
        Rectangle {
            id: card
            required property var modelData
            width:root.width;height:cardContent.implicitHeight+20;radius:6
            color:Qt.rgba(Color.foreground.r,Color.foreground.g,Color.foreground.b,modelData.room===null?0.09:0.035)
            Column {
                id:cardContent
                anchors {left:parent.left;right:parent.right;top:parent.top;margins:10}
                spacing:7
                RockButton {visible:card.modelData.room===null;text:(root.expanded[String(card.modelData.floor)]?"▾ Hide rooms":"▸ Show rooms");height:28;onClicked:{var e=Object.assign({},root.expanded);e[String(card.modelData.floor)]=!e[String(card.modelData.floor)];root.expanded=e}}
                Text {text:card.modelData.name+(card.modelData.room===null?"":"  ·  "+card.modelData.floorName);color:Color.foreground;font.family:Style.font.family;font.pixelSize:12;font.bold:card.modelData.room===null}
                Column {
                    width:parent.width
                    visible:card.modelData.room===null
                    spacing:6
                    Text {width:parent.width;text:"RECORDED FLOOR ACTIVITY · "+(card.modelData.activity||[]).length+" runs · room coverage / mode unverified";color:Color.accent;font.family:Style.font.family;font.pixelSize:10;wrapMode:Text.WordWrap}
                    Rectangle {
                        width:Math.max(120,root.width-365);height:23;x:52;radius:3;clip:true
                        color:Qt.rgba(Color.foreground.r,Color.foreground.g,Color.foreground.b,0.06)
                        Rectangle {x:parent.width/2;width:1;height:parent.height;color:Color.accent;opacity:0.6}
                        Repeater {
                            model:(card.modelData.activity||[]).filter(function(r){return r.begin>=Date.now()/1000-7*86400 && r.begin<=Date.now()/1000+7*86400})
                            Rectangle {
                                required property var modelData
                                x:Math.max(0,Math.min(parent.width-5,parent.width/2+(modelData.begin-Date.now()/1000)/86400/14*parent.width))
                                width:Math.max(5,Math.min(parent.width-x,(Math.max(0,(modelData.end||modelData.begin)-modelData.begin))/86400/14*parent.width));height:13;anchors.verticalCenter:parent.verticalCenter;radius:2
                                color:modelData.complete===1?Color.accent:"#ed8796"
                            }
                        }
                    }
                    Repeater {
                        model:card.modelData.activity||[]
                        Text {
                            required property var modelData
                            width:parent.width
                            text:new Date(modelData.begin*1000).toLocaleString(Qt.locale("en_GB"),"ddd d MMM HH:mm")+(modelData.end?"–"+new Date(modelData.end*1000).toLocaleTimeString(Qt.locale("en_GB"),"HH:mm"):"")+"  ·  "+(typeof modelData.duration==="number"?Math.round(modelData.duration/60)+" min":"duration unknown")+"  ·  "+(typeof modelData.area==="number"?(modelData.area/1000000).toFixed(1)+" m²":"area unknown")+"  ·  "+(modelData.complete===1?"Run complete":"Completion unconfirmed")
                            color:Color.foreground;opacity:0.8;font.family:Style.font.family;font.pixelSize:10;wrapMode:Text.WordWrap
                        }
                    }
                }
                Repeater {
                    model:card.modelData.lanes
                    Row {
                        required property var modelData
                        width:parent.width;spacing:8
                        Text {width:44;text:modelData.mode==="mop"?"MOP":"VAC";color:Color.accent;font.family:Style.font.family;font.pixelSize:10;anchors.verticalCenter:parent.verticalCenter}
                        Rectangle {
                            width:Math.max(120,root.width-365);height:28;radius:3
                            color:Qt.rgba(Color.foreground.r,Color.foreground.g,Color.foreground.b,0.055)
                            Rectangle {x:parent.width/2;width:1;height:parent.height;color:Color.accent;opacity:0.6}
                            Rectangle {visible:modelData.due!==null;x:Math.max(3,Math.min(parent.width-8,parent.width/2+(modelData.due-Date.now()/1000)/86400/14*parent.width));width:6;height:6;radius:3;anchors.verticalCenter:parent.verticalCenter;color:modelData.status==="overdue"?"#ed8796":Color.accent}
                            Text {anchors.left:parent.left;anchors.leftMargin:6;anchors.verticalCenter:parent.verticalCenter;text:modelData.days?"Every "+modelData.days+"d · "+new Date(modelData.due*1000).toLocaleDateString(Qt.locale("en_GB"),"d MMM"):"No plan · last clean unknown";color:Color.foreground;font.family:Style.font.family;font.pixelSize:9}
                        }
                        RockButton {text:"Reminder";height:28;onClicked:{root.editing={floor:card.modelData.floor,room:card.modelData.room,mode:modelData.mode};root.intervalDays=modelData.days||7}}
                        RockButton {text:"Clean now";height:28;onClicked:root.cleanRequested(card.modelData.floor,card.modelData.room,modelData.mode)}
                    }
                }
            }
        }
    }
        }
        Rectangle {anchors.right:parent.right;width:4;radius:2;color:Color.accent;opacity:0.55;visible:roomScroll.contentHeight>roomScroll.height;height:Math.max(20,roomScroll.height*roomScroll.visibleArea.heightRatio);y:roomScroll.visibleArea.yPosition*roomScroll.height}
    }
    Column {
        visible:root.editing!==null;width:parent.width;spacing:8
        Text {text:"Local reminder interval · "+(root.editing?root.editing.mode:"");color:Color.accent;font.family:Style.font.family;font.pixelSize:13}
        Flow {width:parent.width;spacing:6;Repeater {model:[0,1,2,3,7,14,30];RockButton {required property int modelData;text:modelData?modelData+" days":"Off";selected:root.intervalDays===modelData;onClicked:root.intervalDays=modelData}}}
        Row {spacing:8;RockButton {text:"Cancel";onClicked:root.editing=null} RockButton {text:"Save reminder";primary:true;available:!saver.running;onClicked:{var p=Object.assign({},root.editing,{days:root.intervalDays});saver.command=[root.python,root.base+"/omarock.py","save-plan","--request",JSON.stringify(p)];saver.running=true}}}
    }
    Text {width:parent.width;text:root.message||"Past room/mode coverage cannot yet be verified from imported Roborock history. Unknown is not overdue. Dots show planned due dates, not completed cleans. Clean now opens review; it does not start the robot.";color:Color.foreground;opacity:0.6;font.family:Style.font.family;font.pixelSize:10;wrapMode:Text.WordWrap}
    Process {id:saver;stdout:StdioCollector {onStreamFinished:{try{var v=JSON.parse(text);if(v.error)root.message=v.error;else{root.rows=v.rows;root.editing=null;root.message="Plan saved locally. Automatic cleaning is disabled."}}catch(e){root.message="Plan could not be saved"}}}}
}
