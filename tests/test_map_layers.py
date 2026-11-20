import unittest
from types import SimpleNamespace as S
from vacuum_map_parser_base.map_data import Point, Area, ImageDimensions
import map_layers
class Layers(unittest.TestCase):
 def data(self):return S(image=S(dimensions=ImageDimensions(0,0,100,100,2,0,lambda p:p)))
 def test_empty(self):
  r=map_layers.serialize(self.data());self.assertEqual(r['path'],[]);self.assertEqual(r['obstacles'],[])
 def test_crop_transform(self):
  d=self.data();d.obstacles=[Point(10,20)]
  self.assertEqual(map_layers.serialize(d,3,5)['obstacles'],[[17,153]])
 def test_separate_paths_restrictions(self):
  d=self.data();d.path=S(path=[[Point(1,2),Point(3,4)]]);d.no_go_areas=[Area(1,2,3,4,5,6,7,8)]
  r=map_layers.serialize(d);self.assertEqual(len(r['path'][0]['points']),2);self.assertEqual(len(r['restrictions'][0]['points']),4)
