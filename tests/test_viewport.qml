// Synthetic Qt transform regression; does not load robot state or send commands.
// Run: QT_QPA_PLATFORM=offscreen qml6 tests/test_viewport.qml
import QtQuick
import "../RoomGeometry.js" as RoomGeometry

Item {
    id: viewport
    width: 600; height: 400
    property real zoom: 1
    property real panX: 0
    property real panY: 0
    Item {
        id: plane
        width: 400; height: 200
        anchors.centerIn: parent
        transform: [
            Scale { origin.x: plane.width/2; origin.y: plane.height/2; xScale: viewport.zoom; yScale: viewport.zoom },
            Translate { x: viewport.panX; y: viewport.panY }
        ]
    }
    function near(actual, expected) {
        if (Math.abs(actual-expected)>0.00001) throw new Error(actual+" != "+expected)
    }
    Component.onCompleted: Qt.callLater(function() {
        try {
            var count=0
            var mask={coordinateFrame:"cropped-image-pixels",rooms:[{id:16,rects:[[20,10,40,30]]}]}
            // Match production painted-plane -> source-image conversion (2x source).
            for (var state of [[1,0,0],[1.5625,90,-30],[5,-250,120]]) {
                viewport.zoom=state[0]; viewport.panX=state[1]; viewport.panY=state[2]
                for (var source of [[30,20],[100,80],[0,0],[800,400]]) {
                    var screen=plane.mapToItem(viewport,source[0]/2,source[1]/2)
                    var local=plane.mapFromItem(viewport,screen.x,screen.y)
                    near(local.x*2,source[0]); near(local.y*2,source[1])
                    var hit=RoomGeometry.roomAt(mask,[{id:16}],local.x*2,local.y*2)
                    if(hit!==(source[0]===30 ? 16 : null)) throw new Error("Transformed room pick mismatch")
                    count+=3
                }
            }
            console.log(count+" synthetic Qt transform/room assertions passed; not physical pointer/touch proof")
            Qt.exit(0)
        } catch(e) { console.error(e); Qt.exit(1) }
    })
}
