import QtQuick
import QtQuick.Controls
import Quickshell.Io
import qs.Commons
Column {
    id: pane
    property string python: ""
    property string base: ""
    property int floor: -1
    property var rooms: []
    property var preferences: ({})
    property int room: -1
    property string message: ""
    signal useDefault(int roomId, string mode)
    width: parent.width
    spacing: 8
    onFloorChanged: {room=-1;load()}
    Component.onCompleted: load()
    function load() { if(python && base && !reader.running)reader.running=true }
    function edit(id) {
        room=id
        var v=preferences[String(floor)+":"+String(id)]||{}
        alias.text=v.alias||""; notes.text=v.notes||""
        mode.currentIndex=Math.max(0,["vacuum","vacuum_and_mop","mop"].indexOf(v.mode||"vacuum"))
        message=""
    }
    Process {
        id: reader
        command:[pane.python,pane.base+"/omarock.py","room-preferences"]
        stdout: StdioCollector {onStreamFinished:{try{pane.preferences=JSON.parse(text).preferences||{}}catch(e){pane.message="Could not load local preferences"}}}
    }
    Process {
        id: writer
        stdout: StdioCollector {onStreamFinished:{try{var v=JSON.parse(text);pane.message=v.error||"Saved locally. Robot and cloud room names unchanged.";if(!v.error)pane.preferences=v.preferences}catch(e){pane.message="Save failed"}}}
    }
    Text {text:"Room notebook";color:Color.foreground;font.pixelSize:18}
    Text {width:parent.width;text:"Private aliases, notes and default modes per floor/room. Defaults only prepare a review; they never start cleaning.";color:Color.foreground;wrapMode:Text.WordWrap;font.pixelSize:11}
    Flow {
        width:parent.width;spacing:6
        Repeater {model:pane.rooms;RockButton {required property var modelData;text:((pane.preferences[String(pane.floor)+":"+String(modelData.id)]||{}).alias||modelData.name);selected:pane.room===modelData.id;onClicked:pane.edit(modelData.id)}}
    }
    Column {
        width:parent.width;spacing:6;visible:pane.room!==-1
        Text {text:"Cloud name: "+((pane.rooms.find(function(r){return r.id===pane.room})||{}).name||"Unknown");color:Color.foreground;font.pixelSize:12}
        TextField {id:alias;width:parent.width;placeholderText:"Local alias (optional)";maximumLength:80}
        TextField {id:notes;width:parent.width;placeholderText:"Room notes (up to 1,000 characters)";maximumLength:1000}
        ComboBox {id:mode;model:["Vacuum","Vacuum & mop","Mop"];width:220}
        Row {spacing:8
            RockButton {text:writer.running?"Saving…":"Save locally";available:!writer.running;onClicked:{
                writer.command=[pane.python,pane.base+"/omarock.py","save-room-preference","--request",JSON.stringify({floor:pane.floor,room:pane.room,alias:alias.text,notes:notes.text,mode:["vacuum","vacuum_and_mop","mop"][mode.currentIndex]})];writer.running=true
            }}
            RockButton {text:"Use saved default";available:!!pane.preferences[String(pane.floor)+":"+String(pane.room)];onClicked:pane.useDefault(pane.room,pane.preferences[String(pane.floor)+":"+String(pane.room)].mode)}
        }
    }
    Text {width:parent.width;text:pane.message;color:Color.accent;wrapMode:Text.WordWrap}
}
