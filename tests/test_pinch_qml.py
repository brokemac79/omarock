"""Synthetic native multi-touch against the extracted production PinchHandler."""
import os,shutil,subprocess,tempfile,unittest
from pathlib import Path
R=Path(__file__).resolve().parents[1]
RUNNER=shutil.which('qmltestrunner') or '/usr/lib/qt6/bin/qmltestrunner'
@unittest.skipUnless(Path(RUNNER).is_file(),'Qt Quick Test runner unavailable')
class PinchTests(unittest.TestCase):
 def test_production_pinch(self):
  source=(R/'RockPanel.qml').read_text();start=source.index('                                    PinchHandler {');pos=source.index('{',start);depth=1;end=pos+1
  while depth:
   if source[end]=='{':depth+=1
   elif source[end]=='}':depth-=1
   end+=1
  handler=source[start:end]
  qml='''import QtQuick
import QtTest
Item {
 id: root
 width:600;height:400
 Rectangle {
  id:mapViewport
  anchors.fill:parent
  color:"black"
  property real zoom:1
  HANDLER
 }
 TestCase {
  name:"ProductionPinch"
  when:windowShown
  function test_two_fingers_scale() {
   var touch=touchEvent(root)
   touch.press(0,root,240,200).press(1,root,360,200).commit()
   wait(30)
   for(var n=1;n<=6;n++){touch.move(0,root,240-n*10,200).move(1,root,360+n*10,200).commit();wait(20)}
   verify(mapViewport.zoom>1.1,"Pinch must increase production zoom: "+mapViewport.zoom)
   verify(mapViewport.zoom<=5,"Zoom must remain bounded")
   touch.release(0,root).release(1,root).commit()
  }
 }
}'''.replace('HANDLER',handler)
  with tempfile.TemporaryDirectory() as d:
   Path(d,'tst_pinch.qml').write_text(qml)
   result=subprocess.run([RUNNER,'-input',d],env=dict(os.environ,QT_QPA_PLATFORM='offscreen'),capture_output=True,text=True,timeout=30)
   self.assertEqual(result.returncode,0,result.stdout+result.stderr)
