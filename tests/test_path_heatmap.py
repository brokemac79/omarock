import unittest
from path_heatmap import build
C=[{'map':{'x':x,'y':y},'vacuum':{'x':x*100,'y':y*100}} for x,y in [(0,0),(1,0),(0,1)]]
class HeatmapTests(unittest.TestCase):
 def capture(self,**kwargs):return {'floor':0,'at':'2026-11-20T10:00:00+00:00','calibration':C,'paths':[{'kind':'path','points':[[0,0],[2,0]]}]}|kwargs
 def test_empty_not_zero_coverage(self):
  d=build([],0,C,1795170000);self.assertFalse(d['available']);self.assertNotIn('coverage',d)
 def test_reprojects_crop_and_keeps_modes_honest(self):
  frame=[{'map':{'x':p['map']['x']+10,'y':p['map']['y']+5},'vacuum':p['vacuum']} for p in C]
  d=build([self.capture()],0,frame,1795170000)
  self.assertTrue(d['available']);self.assertGreaterEqual(d['cells'][0]['points'][0][0],10)
  self.assertEqual({c['kind'] for c in d['cells']},{'path'})
 def test_other_floor_and_future_rejected(self):
  self.assertFalse(build([self.capture(floor=1)],0,C,1795170000)['available'])
  self.assertFalse(build([self.capture(at='2030-01-01T00:00:00+00:00')],0,C,1795170000)['available'])
 def test_bad_calibration_fails_closed(self):self.assertFalse(build([self.capture()],0,[C[0]]*3,1795170000)['available'])
 def test_mop_not_vacuum(self):
  d=build([self.capture(paths=[{'kind':'mop_path','points':[[0,0],[2,0]]}])],0,C,1795170000)
  self.assertEqual({c['kind'] for c in d['cells']},{'mop_path'})
