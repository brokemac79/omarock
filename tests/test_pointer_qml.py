"""Exercise the production MouseArea with synthetic Qt events, never robot state."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1]
RUNNER = shutil.which("qmltestrunner") or "/usr/lib/qt6/bin/qmltestrunner"


@unittest.skipUnless(Path(RUNNER).is_file(), "Qt Quick Test runner unavailable")
class ProductionPointerTests(unittest.TestCase):
    def test_production_pointer_handlers(self):
        panel = (SOURCE / "RockPanel.qml").read_text()
        start = panel.index("                                        MouseArea {")
        end = panel.index("\n                                    }", start)
        area = panel[start:end].strip()
        # Fail loudly if extraction boundaries drift; do not silently test a copy.
        self.assertTrue(area.endswith("}"))
        qml = r'''
import QtQuick
import QtTest
import "RoomGeometry.js" as RoomGeometry
Item {
 id: root
 width: 600; height: 400
 property int scope: 0
 property bool activeFloor: true
 property var zones: []
 property int selectedZone: -1
 property bool panMode: false
 property var draft: null
 property string actionMessage: ""
 property int selectedRoom: -1
 property var floorMap: ({roomMaskPixels:{coordinateFrame:"cropped-image-pixels",rooms:[{id:16,rects:[[100,60,100,60]]}]}})
 property var current: ({rooms:[{id:16}]})
 function chooseRoom(id) {selectedRoom=id}
 QtObject {id: mapImage; property int status: Image.Ready; property size sourceSize: Qt.size(800,400)}
 QtObject {id: mapCanvas; function requestPaint() {}}
 Item {
  id: mapViewport
  anchors.fill: parent
  property real zoom: 1
  property real panX: 0
  property real panY: 0
  Item {
   id: plane
   width:400; height:200
   anchors.centerIn: parent
   transform: [
    Scale {origin.x:plane.width/2; origin.y:plane.height/2; xScale:mapViewport.zoom; yScale:mapViewport.zoom},
    Translate {x:mapViewport.panX; y:mapViewport.panY}
   ]
   __AREA__
  }
 }
 TestCase {
  name:"ProductionMapPointer"
  when:windowShown
  function init() {
   root.scope=0;root.activeFloor=true;root.zones=[];root.selectedZone=-1;root.draft=null;root.selectedRoom=-1
   mapViewport.zoom=1;mapViewport.panX=0;mapViewport.panY=0
  }
  function point(x,y) {return plane.mapToItem(root,x/2,y/2)}
  function test_room_at_transformed_cell() {
   for(var state of [[1,0,0],[1.5625,90,-30],[2,80,40]]) {
    mapViewport.zoom=state[0];mapViewport.panX=state[1];mapViewport.panY=state[2]
    var p=point(150,90)
    root.selectedRoom=-1
    mouseClick(root,p.x,p.y,Qt.LeftButton)
    compare(root.selectedRoom,16)
    p=point(220,90);root.selectedRoom=-1
    mouseClick(root,p.x,p.y,Qt.LeftButton)
    compare(root.selectedRoom,-1)
   }
  }
  function test_zone_source_coordinates() {
   root.scope=2;mapViewport.zoom=1.5625;mapViewport.panX=50;mapViewport.panY=20
   var a=point(150,90),b=point(250,150)
   mousePress(root,a.x,a.y,Qt.LeftButton)
   mouseMove(root,b.x,b.y,20)
   mouseRelease(root,b.x,b.y,Qt.LeftButton)
   compare(root.zones.length,1)
   var expected=[150,90,250,150]
   for(var i=0;i<4;i++)verify(Math.abs(root.zones[0][i]-expected[i])<2)
   compare(root.draft,null)
  }
  function test_inactive_floor_cannot_draw() {
   root.scope=2;root.activeFloor=false
   var a=point(150,90),b=point(250,150)
   mousePress(root,a.x,a.y,Qt.LeftButton);mouseMove(root,b.x,b.y,20);mouseRelease(root,b.x,b.y,Qt.LeftButton)
   compare(root.zones.length,0)
  }
  function test_select_and_resize_one_zone() {
   root.scope=2;root.zones=[[150,90,250,150],[300,100,400,190]]
   var p=point(340,145)
   mouseClick(root,p.x,p.y,Qt.LeftButton)
   compare(root.selectedZone,1)
   var a=point(400,190),b=point(450,230)
   mousePress(root,a.x,a.y,Qt.LeftButton);mouseMove(root,b.x,b.y,20);mouseRelease(root,b.x,b.y,Qt.LeftButton)
   compare(root.zones.length,2)
   compare(root.zones[0],[150,90,250,150])
   compare(root.zones[1],[300,100,450,230])
  }
  function test_right_drag_pan() {
   mapViewport.zoom=1.5625
   var a=point(300,180)
   mousePress(root,a.x,a.y,Qt.RightButton)
   mouseMove(root,a.x+40,a.y+25,20)
   mouseRelease(root,a.x+40,a.y+25,Qt.RightButton)
   verify(Math.abs(mapViewport.panX-40)<2)
   verify(Math.abs(mapViewport.panY-25)<2)
   compare(root.zones.length,0)
  }
 }
}
'''
        with tempfile.TemporaryDirectory(prefix="omarock-pointer-") as tmp:
            target = Path(tmp)
            (target / "RoomGeometry.js").write_text((SOURCE / "RoomGeometry.js").read_text())
            (target / "tst_pointer.qml").write_text(qml.replace("__AREA__", area))
            result = subprocess.run([RUNNER, "-input", str(target)], env={**os.environ, "QT_QPA_PLATFORM": "offscreen"}, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
