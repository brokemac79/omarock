import QtQuick
import Quickshell.Io
import qs.Commons
Column {
    id:root
    property string python
    property string base
    property var maps: []
    property var jobs: []
    property int floor: maps.length?maps[0].id:-1
    property var room: null
    property string mode: "vacuum"
    property int hour:10
    property int minute:0
    property var weekdays:[0,1,2,3,4,5,6]
    property bool controlsEnabled:false
    property bool enableJob:false
    property string message:""
    spacing:10
    onVisibleChanged:if(visible)reload()
    function reload(){reader.running=true}
    Process {id:reader;command:[root.python,root.base+"/omarock.py","schedules"];stdout:StdioCollector {onStreamFinished:{try{var v=JSON.parse(text);root.jobs=v.schedules||[];root.controlsEnabled=v.controlsEnabled===true}catch(e){root.message="Cannot load schedules"}}}}
    Process {id:writer;stdout:StdioCollector {onStreamFinished:{try{var v=JSON.parse(text);if(v.error)root.message=v.error;else{root.jobs=v.schedules;root.enableJob=false;root.message="Saved. Disabled jobs will not run."}}catch(e){root.message="Schedule update outcome unknown; reload before retrying"}}}}
    Text {text:"Timed cleaning";color:Color.foreground;font.family:Style.font.family;font.pixelSize:23}
    Text {width:parent.width;text:"Desktop scheduler · Europe/London (GMT/BST). Surface must be awake, signed in and online. Missed times are skipped, not replayed. Jobs never switch floor maps. This does not create timers in the Roborock phone app.";color:Color.accent;font.family:Style.font.family;font.pixelSize:11;wrapMode:Text.WordWrap}
    Flow {width:parent.width;spacing:6;Repeater {model:root.maps;RockButton {required property var modelData;text:modelData.name;selected:root.floor===modelData.id;onClicked:{root.floor=modelData.id;root.room=null}}}}
    Flow {width:parent.width;spacing:6;RockButton {text:"Whole floor";selected:root.room===null;onClicked:root.room=null} Repeater {model:(root.maps.find(function(m){return m.id===root.floor})||{}).rooms||[];RockButton {required property var modelData;text:modelData.name;selected:root.room===modelData.id;onClicked:root.room=modelData.id}}}
    Row {spacing:6;RockButton {text:"Vacuum";selected:root.mode==="vacuum";onClicked:root.mode="vacuum"} RockButton {text:"Mop";selected:root.mode==="mop";onClicked:root.mode="mop"}}
    Row {spacing:8;RockButton {text:"Hour −";onClicked:root.hour=(root.hour+23)%24} Text {text:String(root.hour).padStart(2,"0")+":"+String(root.minute).padStart(2,"0");color:Color.foreground;font.family:Style.font.family;font.pixelSize:18;anchors.verticalCenter:parent.verticalCenter} RockButton {text:"Hour +";onClicked:root.hour=(root.hour+1)%24} RockButton {text:"Min −";onClicked:root.minute=(root.minute+55)%60} RockButton {text:"Min +";onClicked:root.minute=(root.minute+5)%60}}
    Row {spacing:5;Repeater {model:["Mon","Tue","Wed","Thu","Fri","Sat","Sun"];RockButton {required property string modelData;required property int index;text:modelData;selected:root.weekdays.indexOf(index)>=0;onClicked:{var d=root.weekdays.slice();var n=d.indexOf(index);if(n<0)d.push(index);else d.splice(n,1);root.weekdays=d}}}}
    Text {width:parent.width;text:root.controlsEnabled?"Before enabling: leave the robot physically on the selected floor with that map active. A job operates the robot automatically at the chosen time.":"Automatic starts are locked until supervised cleaning controls are commissioned. You can save disabled schedules now.";color:Color.accent;font.family:Style.font.family;font.pixelSize:11;wrapMode:Text.WordWrap}
    RockButton {text:(root.enableJob?"✓ ":"□ ")+"Enable automatic cleaning; robot will be on this floor";available:root.controlsEnabled;selected:root.enableJob;onClicked:root.enableJob=!root.enableJob}
    Row {spacing:8;RockButton {text:"Save schedule";primary:true;available:!writer.running && root.weekdays.length>0;onClicked:{writer.command=[root.python,root.base+"/omarock.py","save-schedule","--request",JSON.stringify({floor:root.floor,room:root.room,mode:root.mode,hour:root.hour,minute:root.minute,weekdays:root.weekdays,enabled:root.enableJob,confirmed:root.enableJob})];writer.running=true}} RockButton {text:"Reload";onClicked:root.reload()}}
    Text {text:root.message;color:Color.accent;font.family:Style.font.family;font.pixelSize:11}
    Repeater {model:root.jobs;Row {required property var modelData;spacing:8
        Text {width:root.width-100;text:(modelData.enabled?"ENABLED":"DISABLED")+" · "+(root.maps.find(function(m){return m.id===modelData.floor})||{}).name+" · "+(modelData.room===null?"whole floor":"room "+modelData.room)+" · "+modelData.mode+" · "+String(modelData.hour).padStart(2,"0")+":"+String(modelData.minute).padStart(2,"0")+" · "+modelData.weekdays.map(function(d){return ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"][d]}).join(", ");color:Color.foreground;font.family:Style.font.family;font.pixelSize:11;wrapMode:Text.WordWrap}
        RockButton {text:"Delete";available:!writer.running;onClicked:{writer.command=[root.python,root.base+"/omarock.py","delete-schedule","--request",JSON.stringify({id:modelData.id})];writer.running=true}}
    }}
}
