import QtQuick
import qs.Commons
Column {
    id:root
    property var records:[]
    property var maps:[]
    property int floor:-1
    property string search:""
    property int page:0
    property var selected:null
    readonly property var filtered:records.filter(function(r){return (root.floor===-1 || r.map_flag===root.floor) && (root.floorName(r.map_flag)+" "+root.date(r.begin)+" "+String(r.area_ids||[])).toLowerCase().indexOf(root.search.toLowerCase())>=0})
    function floorName(id){var f=maps.find(function(m){return m.id===id});return f?f.name:"Unknown floor"}
    function date(s){return s?new Date(s*1000).toLocaleString(Qt.locale("en_GB"),"ddd d MMM yyyy HH:mm"):"Unknown"}
    onFloorChanged:page=0
    onSearchChanged:page=0
    onRecordsChanged:page=Math.min(page,Math.max(0,Math.ceil(filtered.length/15)-1))
    spacing:10
    Text {text:"Cleaning archive";color:Color.foreground;font.family:Style.font.family;font.pixelSize:23}
    Text {width:parent.width;text:"Locally retained for 120 days from available device history. Older runs cannot be invented. Room IDs and vacuum/mop attribution remain unknown when absent.";color:Color.accent;font.family:Style.font.family;font.pixelSize:11;wrapMode:Text.WordWrap}
    Flow {width:parent.width;spacing:5;RockButton {text:"All floors";selected:root.floor===-1;onClicked:root.floor=-1} Repeater {model:root.maps;RockButton {required property var modelData;text:modelData.name;selected:root.floor===modelData.id;onClicked:root.floor=modelData.id}}}
    Rectangle {width:parent.width;height:34;radius:4;color:Qt.rgba(Color.foreground.r,Color.foreground.g,Color.foreground.b,0.08)
        TextInput {id:query;anchors.fill:parent;anchors.margins:8;color:Color.foreground;font.family:Style.font.family;font.pixelSize:12;clip:true;selectByMouse:true;onTextChanged:root.search=text}
        Text {anchors.fill:query;visible:!query.text && !query.activeFocus;text:"Search floor, date or reported room ID…";color:Color.foreground;opacity:0.5;font.family:Style.font.family;font.pixelSize:12}
    }
    Row {spacing:8;RockButton {text:"← Previous";available:root.page>0;onClicked:root.page--} Text {text:root.filtered.length+" runs · page "+(root.page+1)+" / "+Math.max(1,Math.ceil(root.filtered.length/15));color:Color.foreground;font.family:Style.font.family;font.pixelSize:11;anchors.verticalCenter:parent.verticalCenter} RockButton {text:"Next →";available:(root.page+1)*15<root.filtered.length;onClicked:root.page++}}
    Repeater {model:root.filtered.slice(root.page*15,(root.page+1)*15);Rectangle {
        required property var modelData
        width:root.width;height:62;radius:4;color:Qt.rgba(Color.foreground.r,Color.foreground.g,Color.foreground.b,0.05)
        Column {anchors {left:parent.left;right:parent.right;verticalCenter:parent.verticalCenter;margins:10}
        spacing:6
            Text {text:root.floorName(modelData.map_flag)+" · "+root.date(modelData.begin);color:Color.foreground;font.family:Style.font.family;font.pixelSize:12}
            Text {text:(typeof modelData.area==="number"?(modelData.area/1000000).toFixed(1)+" m²":"Area unknown")+" · "+(typeof modelData.duration==="number"?Math.round(modelData.duration/60)+" min":"Duration unknown")+" · "+(modelData.complete===1?"Run complete":"Completion unconfirmed")+" · tap for details";color:Color.accent;font.family:Style.font.family;font.pixelSize:10}
        }
        MouseArea {anchors.fill:parent;onClicked:root.selected=modelData}
    }}
    Rectangle {visible:root.selected!==null;width:parent.width;height:details.implicitHeight+24;radius:5;color:Qt.rgba(Color.accent.r,Color.accent.g,Color.accent.b,0.1)
        Column {id:details;anchors {left:parent.left;right:parent.right;top:parent.top;margins:12}
        spacing:8
            Text {width:parent.width;text:root.selected?"Start: "+root.date(root.selected.begin)+"\nEnd: "+root.date(root.selected.end)+"\nReported room IDs: "+((root.selected.area_ids||[]).length?root.selected.area_ids.join(", "):"unknown")+"\nMop washes: "+(root.selected.wash_count===undefined || root.selected.wash_count===null?"unknown":root.selected.wash_count)+"\nCleaning mode / whole-floor coverage: unverified":"";color:Color.foreground;font.family:Style.font.family;font.pixelSize:12;wrapMode:Text.WordWrap}
            RockButton {text:"Close details";onClicked:root.selected=null}
        }
    }
}
