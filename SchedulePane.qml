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
    signal cleanRequested(var floorId,var roomId,string cleanMode)
    spacing:12
    Text {text:"Cleaning rhythm";color:Color.foreground;font.family:Style.font.family;font.pixelSize:24;font.bold:true}
    Text {width:parent.width;text:"Per floor. Per room. Vacuum and mop, independently. Local plans only — no automatic dispatch.";color:Color.accent;font.family:Style.font.family;font.pixelSize:11;wrapMode:Text.WordWrap}
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
    Repeater {
        model:root.rows.filter(function(r){return root.filterFloor===-1 || root.filterFloor===r.floor})
        Rectangle {
            id: card
            required property var modelData
            width:root.width;height:112;radius:6
            color:Qt.rgba(Color.foreground.r,Color.foreground.g,Color.foreground.b,modelData.room===null?0.09:0.035)
            Column {
                anchors.fill:parent;anchors.margins:10;spacing:7
                Text {text:card.modelData.name+(card.modelData.room===null?"":"  ·  "+card.modelData.floorName);color:Color.foreground;font.family:Style.font.family;font.pixelSize:12;font.bold:card.modelData.room===null}
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
                        RockButton {text:"Edit";height:28;onClicked:{root.editing={floor:card.modelData.floor,room:card.modelData.room,mode:modelData.mode};root.intervalDays=modelData.days||7}}
                        RockButton {text:"Clean now";height:28;onClicked:root.cleanRequested(card.modelData.floor,card.modelData.room,modelData.mode)}
                    }
                }
            }
        }
    }
    Column {
        visible:root.editing!==null;width:parent.width;spacing:8
        Text {text:"Repeat interval · "+(root.editing?root.editing.mode:"");color:Color.accent;font.family:Style.font.family;font.pixelSize:13}
        Flow {width:parent.width;spacing:6;Repeater {model:[0,1,2,3,7,14,30];RockButton {required property int modelData;text:modelData?modelData+" days":"Off";selected:root.intervalDays===modelData;onClicked:root.intervalDays=modelData}}}
        Row {spacing:8;RockButton {text:"Cancel";onClicked:root.editing=null} RockButton {text:"Save plan";primary:true;available:!saver.running;onClicked:{var p=Object.assign({},root.editing,{days:root.intervalDays});saver.command=[root.python,root.base+"/omarock.py","save-plan","--request",JSON.stringify(p)];saver.running=true}}}
    }
    Text {width:parent.width;text:root.message||"Past room/mode coverage cannot yet be verified from imported Roborock history. Unknown is not overdue. Dots show planned due dates, not completed cleans. Clean now opens review; it does not start the robot.";color:Color.foreground;opacity:0.6;font.family:Style.font.family;font.pixelSize:10;wrapMode:Text.WordWrap}
    Process {id:saver;stdout:StdioCollector {onStreamFinished:{try{var v=JSON.parse(text);if(v.error)root.message=v.error;else{root.rows=v.rows;root.editing=null;root.message="Plan saved locally. Automatic cleaning is disabled."}}catch(e){root.message="Plan could not be saved"}}}}
}
